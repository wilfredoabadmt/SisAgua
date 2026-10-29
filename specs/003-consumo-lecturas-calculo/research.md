# Investigación Técnica y Decisiones de Arquitectura: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 0 — Investigación y Decisiones Técnicas  
> **Fecha:** Octubre 2026  

---

## 1. Decisiones de Arquitectura y Diseño

### DEC-015: Creación del Módulo Especializado `apps/consumo`
- **Contexto:** Las mediciones mensuales y la facturación de agua tienen alta frecuencia transaccional e involucran reglas de monotonicidad física y cálculos volumétricos.
- **Alternativas:**
  1. *Mezclar lecturas dentro de `apps/medidores`:* Generaría acoplamiento excesivo entre la gestión del activo físico de inventario y los procesos mensuales de lectura y consumo.
  2. *Crear app dedicada `apps/consumo`:* Separa claramente el ciclo de captura de lecturas, validaciones, proformas y cálculo mensual, consumiendo los modelos de `medidores`, `socios` y `servicios`.
- **Decisión:** **Alternativa 2 (App dedicada `apps/consumo`).** Mantiene el principio de separación de responsabilidades (P14) y simplifica los tests y endpoints de campo.

---

### DEC-016: Determinación Determinística de la Lectura Anterior
- **Contexto:** Para calcular el consumo ($\text{Lectura Actual} - \text{Lectura Anterior}$), el sistema debe obtener sin ambigüedad la última lectura válida del medidor en cuestión.
- **Implementación Técnica:**
  - El servicio `obtener_lectura_anterior_valida(medidor, periodo)` ejecuta:
    1. Busca la última `Lectura` no anulada en estado `VALIDADA` o `CORREGIDA` para periodos anteriores a `periodo`:
       ```python
       lectura_previa = Lectura.objects.filter(
           medidor=medidor,
           periodo__lt=periodo,
           estado__in=[EstadoLectura.VALIDADA, EstadoLectura.CORREGIDA]
       ).order_by('-periodo', '-fecha_lectura').first()
       ```
    2. Si existe, retorna su `lectura_actual` y `fecha_lectura`.
    3. Si no existe ninguna lectura mensual previa (ej. primer mes de conexión), consulta la asignación activa del medidor (`AsignacionMedidor`) y retorna su `lectura_instalacion` y `fecha_asignacion`.
    4. Si tampoco existe asignación, recurre a `medidor.lectura_inicial`.
  - Esta cascada determinística garantiza que jamás existan lecturas nulas o no justificadas para medidores en servicio.

---

### DEC-017: Validación de Monotonicidad y Estado `OBSERVADA` (R-DOM-07, P10)
- **Contexto:** Un medidor de agua normal siempre avanza sus metros cúbicos. Una lectura menor a la anterior indica un error de digitación, un daño en el reloj o un cambio físico de dispositivo.
- **Implementación Técnica:**
  - Al capturar la lectura:
    - Si `lectura_actual < lectura_anterior`: el sistema asigna automáticamente `estado = EstadoLectura.OBSERVADA` y `motivo_observacion = "Lectura actual menor a la anterior (R-DOM-07)"`.
    - Si `consumo_calculado > 50` o supera 3 veces el promedio histórico: se marca advertencia de salto inusual.
  - **Bloqueo Constitucional (P10):** Las lecturas observadas quedan estrictamente excluidas de los querysets que alimentan la facturación mensual. No pueden generar deudas exigibles sin intervención autorizada previa.

---

### DEC-018: Reinicio de Contador (*Rollover*) y Sustitución de Medidor
- **Contexto:** Cuando un contador de 5 dígitos mecánicos supera los $99,999 \text{ m}^3$, vuelve a $00000$. En caso de sustitución física por avería, el medidor saliente se retira y se instala uno nuevo.
- **Implementación Técnica:**
  - Si un supervisor valida que ocurrió un *rollover*, el sistema calcula el consumo compensado:
    $$\text{Consumo} = (100000 - \text{Lectura Anterior}) + \text{Lectura Actual}$$
    El registro conserva `es_reinicio_contador = True`, la justificación del supervisor y cambia a `estado = EstadoLectura.CORREGIDA`.
  - En caso de sustitución física durante el mes, la Fase 2 ya contempla la lectura final de retiro y la lectura inicial del nuevo medidor (R-DOM-04).

---

### DEC-019: Motor de Facturación Idempotente y Snapshot de Liquidación (R-DOM-11, R-DOM-12)
- **Contexto:** El proceso de facturación mensual no debe duplicar obligaciones si se corre varias veces (por caídas de red o ejecuciones concurrentes). Además, debe congelar la tarifa aplicada para evitar alteraciones retroactivas si el tarifario cambia en el futuro.
- **Implementación Técnica:**
  - El servicio `facturar_periodo_agua(periodo, usuario)`:
    1. Obtiene el servicio de Agua Potable (`codigo='AGUA'`).
    2. Recorre las lecturas en estado `VALIDADA` o `CORREGIDA` del periodo.
    3. Verifica si ya existe una `Obligacion` con `(socio, servicio, periodo)`:
       - Si existe: incrementa el contador de omitidos (idempotencia garantizada).
       - Si no existe: resuelve la tarifa vigente a la fecha del periodo, calcula el desglose (base, tramos, excedente), computa la fecha de vencimiento según R-DOM-14, y crea la `Obligacion` congelando el snapshot del cálculo en `concepto` y `detalle_snapshot`.
    4. Todo el lote se ejecuta dentro de un contexto de transacción ACID `transaction.atomic()`.

---

### DEC-020: Proforma Informativa sin Carácter Fiscal (R-DOM-09)
- **Contexto:** La proforma entregada al socio notifica la medición efectuada. No es un comprobante de pago ni genera cancelación de saldos.
- **Implementación Técnica:**
  - La vista `proforma_lectura` consulta la lectura del periodo y busca hasta 3 lecturas previas reales del mismo medidor.
  - La plantilla renderiza una constancia limpia imprimible con la leyenda mandataria:
    *"DOCUMENTO INFORMATIVO DE MEDICIÓN — NO CONSTITUYE RECIBO DE PAGO"*.

