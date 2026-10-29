# Decisiones de Diseño y Arquitectura: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## 1. Justificación y Contexto
La Fase 4 materializa el ciclo financiero del sistema (**SisAgua**). El documento funcional ("SISTEMA DE ADMINISTRACIÓN.docx", secciones 2.4 y 9) y la Constitución SDD v1.0 imponen estrictos requerimientos de integridad financiera (P3), idempotencia (P4), conservación histórica (P5), auditoría (P6) y transparencia contable (P8).

---

## 2. Registro de Decisiones de Arquitectura (ADR)

### DEC-021: Arquitectura de la Aplicación `apps/caja`
- **Contexto**: Se requiere separar la contabilidad de cobranza en ventanilla y control de turnos de la lógica de catálogo de servicios y captura de lecturas.
- **Decisión**: Crear la aplicación Django `apps.caja`, responsable de:
  - `CajaTurno`: Control de turnos, fondo de apertura y arqueo diario.
  - `Pago`: Evento de cobro financiero y medio de pago.
  - `Recibo`: Documento legal y fiscal de cobranza emitido al socio.
  - `DetalleRecibo`: Detalle desglosado de obligaciones saldadas en el recibo.
- **Consecuencias**: Mantiene alta cohesión y bajo acoplamiento. Las obligaciones (`apps.servicios.Obligacion`) son consumidas por referencia foránea protegida (`PROTECT`).

---

### DEC-022: Concurrencia y Atomicidad en Cobros (`select_for_update`) (P3, R-DOM-16)
- **Contexto**: Dos cajeros o procesos concurrentes podrían intentar cobrar simultáneamente la misma obligación de un socio.
- **Decisión**: Todo proceso de cobro se ejecutará dentro de un bloque `transaction.atomic()`. Antes de cualquier actualización, las instancias de `Obligacion` seleccionadas serán leídas utilizando `.select_for_update()`:
  ```python
  obligaciones = Obligacion.objects.select_for_update().filter(id__in=obligaciones_ids)
  ```
  Se verificará que todas estén en estado `PENDIENTE`. Si alguna ya no está pendiente, se aborta la transacción y se emite un error explícito.
- **Consecuencias**: Eliminación total de condiciones de carrera y cobros duplicados (P4).

---

### DEC-023: Aplicación Estricta de Cero Pagos Parciales (R-DOM-15)
- **Contexto**: La sección 2.4 de la fuente prohíbe taxativamente abonos parciales sobre una obligación.
- **Decisión**:
  1. En el formulario y la interfaz de usuario, no existe campo de "monto a abonar" por obligación. El usuario solo selecciona qué obligaciones liquidar (checkbox).
  2. En el backend (`services.py`), el servicio valida:
     - Cada obligación se cancela por su `saldo_pendiente` total.
     - El monto total del recibo es la suma exacta de los saldos de las obligaciones seleccionadas.
     - No se permiten importes en 0 ni negativos.
- **Consecuencias**: Cumplimiento del 100% de la regla R-DOM-15.

---

### DEC-024: Numeración Correlativa Inalterable de Recibos (R-DOM-17)
- **Contexto**: Los recibos deben contar con una numeración correlativa única, secuencial y sin saltos arbitrarios.
- **Decisión**:
  - Se genera un campo `numero_recibo` con formato `REC-{año}-{secuencia:06d}` (ej. `REC-2026-000001`).
  - La secuencia anual se determina de forma determinística y atómica dentro de la misma transacción de creación del recibo.
  - Para evitar huecos por números cancelados, los números de recibos emitidos jamás se reúsan ni se eliminan físicamente (P5).
- **Consecuencias**: Trazabilidad fiscal y auditoría intachable.

---

### DEC-025: Mecanismo de Autenticidad y Código QR en Recibos
- **Contexto**: En organizaciones de agua comunitarias, existe riesgo de falsificación de recibos físicos.
- **Decisión**:
  - Cada recibo almacena un `codigo_verificacion` alfanumérico generado criptográficamente (UUID o hash HMAC de 16 caracteres basado en datos clave: número, socio, fecha, monto).
  - La representación del recibo incluye un código QR generado que contiene la URL o identificador de verificación pública de autenticidad:
    `sisagua://recibo/verificar/{numero_recibo}/{codigo_verificacion}`.
- **Consecuencias**: Verificación inmediata por supervisores y socios.

---

### DEC-026: Anulación Autorizada con Reversión Lógica Total (P5, R-DOM-17)
- **Contexto**: Un error de digitación en ventanilla puede requerir anular un recibo.
- **Decisión**:
  - Los modelos `Recibo`, `Pago`, `DetalleRecibo` y `CajaTurno` sobreescriben `delete()` para lanzar `ValidationError` prohibiendo el borrado físico (`DELETE`).
  - El método de anulación `anular_recibo(recibo, usuario, motivo)`:
    - Valida que el usuario tenga el permiso `CAJA:ANULAR`.
    - Exige un motivo documentado de al menos 10 caracteres.
    - Ejecuta un `transaction.atomic()` donde:
      1. El recibo pasa a estado `ANULADO`.
      2. Se registra `usuario_anulacion`, `fecha_anulacion` y `motivo_anulacion`.
      3. Se leen todas las obligaciones vinculadas en sus `DetalleRecibo` con `select_for_update()`.
      4. Cada obligación vuelve a estado `PENDIENTE`, restaurando su `saldo_pendiente = monto`.
      5. Se audita la anulación en `BitacoraAuditoria`.
- **Consecuencias**: Reversión 100% trazable, sin pérdida de datos contables.

---

### DEC-027: Control de Turnos y Arqueo Ciego / Declarativo (Sección 9.5)
- **Contexto**: El cajero debe responder por el dinero físico en su gaveta al inicio y al fin de su turno.
- **Decisión**:
  - Un cajero no puede tener dos turnos abiertos al mismo tiempo.
  - Apertura: Registra `monto_apertura` (fondo de cambio).
  - Cierre: El cajero declara el monto físico en efectivo contado (`monto_declarado_efectivo`).
  - El sistema calcula:
    - `total_efectivo_sistema`: suma de pagos en efectivo recibidos en el turno.
    - `total_digital_sistema`: suma de pagos vía QR y transferencia bancaria.
    - `efectivo_esperado = monto_apertura + total_efectivo_sistema`.
    - `diferencia_efectivo = monto_declarado_efectivo - efectivo_esperado`.
  - Si hay diferencia (sobrante o faltante), se exige justificación en `observaciones_cierre`.
- **Consecuencias**: Control de caja estricto y prevención de fraudes o extravíos.

