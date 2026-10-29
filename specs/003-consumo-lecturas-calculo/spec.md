# Especificación Funcional: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 3 del Orden Canónico de Implementación (Fuente, Sección 15)  
> **Normativa Rector:** Constitución SDD v1.0 (`.specify/memory/constitution.md`)  
> **Fuente Funcional:** `SISTEMA DE ADMINISTRACION.docx` (Secciones 2.1, 2.2, 2.3, 7.1, 7.2, 7.3, 7.4 y 7.5)  
> **Estado:** APROBADA PARA IMPLEMENTACIÓN  

---

## 1. Resumen Ejecutivo y Objetivos de Negocio

La Fase 3 automatiza el ciclo operativo mensual de medición y facturación volumétrica de agua potable. Reemplaza el uso de libretas de campo manuales y cálculos aritméticos en papel por un flujo digital robusto con controles de integridad física y matemática:

1. **Captura Mensual de Lecturas en Campo:** Registro ágil por zona y medidor, resolviendo automáticamente la lectura anterior válida (lectura previa o lectura de instalación).
2. **Validación de Monotonicidad y Detección de Anomalías (R-DOM-07):** Bloqueo nativo e inmediato si la lectura actual es inferior a la anterior ($\text{Lectura Actual} < \text{Lectura Anterior}$), disparando el estado `OBSERVADA` y evitando cobros arbitrarios.
3. **Unicidad de Lectura Definitiva (R-DOM-08):** Una sola lectura válida por medidor y periodo, con auditoría estricta ante correcciones autorizadas.
4. **Proforma Informativa de Medición (R-DOM-09):** Documento imprimible/digital para el socio que muestra el consumo medido y hasta 3 periodos históricos reales, con leyenda obligatoria: *"DOCUMENTO INFORMATIVO DE MEDICIÓN — NO CONSTITUYE RECIBO DE PAGO"*.
5. **Motor Idempotente de Facturación (R-DOM-06, R-DOM-10, R-DOM-11, R-DOM-12):** Emisión masiva o individual de obligaciones de agua, aplicando la tarifa vigente al periodo, calculando vencimientos determinísticos (R-DOM-14) y garantizando que reejecutar el proceso jamás duplique deudas.

---

## 2. Marco Normativo Constitucional Aplicable

| Código | Principio / Regla | Mandato en Fase 3 |
|---|---|---|
| **P1** | Fidelidad de Negocio | El cálculo de agua respeta exactamente la tarifa vigente y sus tramos sin alteración manual. |
| **P2** | Fuente Única de Verdad | La lectura anterior válida proviene del último registro no anulado del mismo medidor. |
| **P3** | Integridad Financiera | La generación de obligaciones de agua se ejecuta en transacciones ACID atómicas. |
| **P4** | Idempotencia | Reintentar la facturación de un periodo jamás generará dos obligaciones para el mismo medidor/mes. |
| **P5** | Conservación Histórica | No se borran lecturas erróneas (`DELETE`). Se corrigen registrando valor anterior, nuevo y motivo. |
| **P6** | Auditoría Verificable | Toda captura, observación, corrección y facturación registra usuario, fecha/hora e IP. |
| **P10** | Validación Previa | Una lectura en estado `OBSERVADA` jamás se factura automáticamente. |
| **R-DOM-06** | Fórmula de Consumo | $\text{Consumo} = \text{Lectura Actual} - \text{Lectura Anterior Válida}$. |
| **R-DOM-07** | Consistencia Monótona | Si $\text{Lectura Actual} < \text{Lectura Anterior}$, se bloquea y marca `OBSERVADA`. |
| **R-DOM-08** | Unicidad Definitiva | Prohibido dos lecturas definitivas para el mismo medidor y periodo mensual. |
| **R-DOM-09** | Proforma Informativa | Constancia de medición informativa sin efectos liberatorios de pago ni carácter fiscal. |
| **R-DOM-10** | No Retroactividad | Aplica la tarifa vigente según fecha del periodo facturado. |
| **R-DOM-11** | Detalle / Snapshot | La obligación congela el desglose del cálculo (mínimo, excedente, tramo, tarifa). |
| **R-DOM-12** | Unicidad Mensual | Solo una obligación de agua por medidor, servicio y periodo `YYYY-MM`. |
| **R-DOM-14** | Vencimiento Determinístico | Vence el día fijado por la institución o el último día natural del mes. |

---

## 3. Historias de Usuario

### US1: Captura de Lecturas Mensuales por Zona y Periodo (Prioridad: CRÍTICA)
**Como** Lector de Campo o Encargado de Medición  
**Quiero** ingresar las lecturas de los medidores de una zona para un periodo mensual determinado  
**Para** registrar el consumo real de agua de los socios de forma rápida y sin errores de transcripción.

- **Criterios de Aceptación:**
  - El usuario selecciona el Periodo (`YYYY-MM`, ej. `2026-10`) y opcionalmente filtra por Zona.
  - El sistema lista los medidores activos asignados a socios en dicha zona.
  - Para cada medidor, el sistema muestra automáticamente:
    - Código de medidor y número de serie.
    - Socio titular y dirección.
    - Lectura anterior válida y fecha de la misma (si es primer periodo, muestra la lectura de instalación).
  - Al ingresar la lectura actual y la fecha de toma, el sistema calcula de inmediato el consumo en metros cúbicos ($m^3$).
  - Si el medidor ya fue leído en este periodo, muestra su lectura y estado.

---

### US2: Validación de Monotonicidad y Lecturas Observadas (Prioridad: CRÍTICA)
**Como** Sistema SisAgua  
**Quiero** validar inmediatamente cada lectura ingresada  
**Para** detectar lecturas inferiores a la anterior, consumos negativos o saltos desproporcionados antes de emitir cobros.

- **Criterios de Aceptación:**
  - Si $\text{Lectura Actual} < \text{Lectura Anterior}$:
    - El sistema bloquea la confirmación estándar y clasifica la lectura automáticamente como `OBSERVADA`.
    - Registra el motivo: *"Lectura actual (X) inferior a la anterior (Y)"*.
    - Impide que dicha lectura pase al proceso de facturación automática (Principio P10).
  - Si el consumo supera 3 veces el promedio histórico del medidor o excede 50 $m^3$:
    - Se marca una advertencia preventiva de *"Consumo Inusual"* para verificación en campo.

---

### US3: Revisión y Corrección Autorizada de Lecturas Observadas (Prioridad: ALTA)
**Como** Supervisor Técnico o Administrador  
**Quiero** revisar las lecturas observadas y corregirlas con justificación documentada  
**Para** resolver errores de dedo, reinicios de contador (*rollover*) o averías sin perder la pista de auditoría.

- **Criterios de Aceptación:**
  - Bandeja especializada de "Lecturas Observadas" filtrable por periodo y zona.
  - El supervisor puede:
    - **Validar con Justificación:** Si se constató reinicio de reloj (*rollover*) o lectura correcta en re-inspección.
    - **Corregir Lectura:** Permite ingresar el valor rectificado, exigiendo ingresar un motivo obligatorio.
    - El registro original jamás se elimina (`DELETE`); se conserva el valor previo, el nuevo y el supervisor responsable (R-DOM-08, P5, P6).
  - Al corregirse/validarse, el estado cambia a `CORREGIDA` o `VALIDADA`, quedando habilitada para facturación.

---

### US4: Emisión de Proforma Informativa de Medición (Prioridad: ALTA)
**Como** Lector o Socio  
**Quiero** generar o consultar la proforma de lectura mensual  
**Para** contar con una constancia de la medición realizada y conocer el consumo registrado.

- **Criterios de Aceptación:**
  - Muestra datos institucionales (nombre, logo, teléfono).
  - Muestra datos del socio (código, nombre, CI, zona, predio) y del medidor (código, serie).
  - Muestra lectura actual, lectura anterior y consumo mensual en $m^3$.
  - Muestra el historial real de consumos de hasta 3 periodos anteriores disponibles.
  - Si no existen 3 periodos previos, muestra solo los reales sin inventar ni duplicar datos (Sección 7.4).
  - Contiene de forma destacada la leyenda: *"DOCUMENTO INFORMATIVO DE MEDICIÓN — NO CONSTITUYE RECIBO DE PAGO"*.

---

### US5: Motor Idempotente de Facturación de Agua (Prioridad: CRÍTICA)
**Como** Administrador o Encargado de Facturación  
**Quiero** ejecutar el proceso mensual de cálculo y emisión de obligaciones de agua para un periodo  
**Para** devengar las cuentas por cobrar oficiales en las cuentas de los socios según las lecturas validadas.

- **Criterios de Aceptación:**
  - Selecciona el Periodo (`YYYY-MM`).
  - Procesa únicamente medidores con lectura en estado `VALIDADA` o `CORREGIDA`.
  - Resuelve la tarifa vigente para el servicio de Agua Potable y la categoría del socio (R-DOM-10).
  - Aplica la fórmula tarifaria (básica, mínimo y tramos excedentes).
  - Genera la `Obligacion` con:
    - `periodo = 'YYYY-MM'`
    - `concepto = 'Consumo de Agua Potable - Periodo YYYY-MM'`
    - `monto = Total Calculado`
    - `saldo_pendiente = Total Calculado`
    - `fecha_vencimiento = R-DOM-14`
    - Snapshot completo de liquidación en `detalle_calculo` (R-DOM-11).
  - **Idempotencia Absoluta (R-DOM-12):** Si la obligación para ese medidor, socio y periodo ya existe, el sistema la omite sin error y no duplica el cobro.
  - Entrega un informe consolidado: total generado en Bs, total de socios facturados, total de lecturas observadas omitidas.

---

### US6: Panel de Cobertura y Monitoreo del Periodo (Prioridad: MEDIA)
**Como** Administrador o Directorio  
**Quiero** visualizar el avance de lectura y facturación del mes  
**Para** saber cuántos medidores han sido leídos, cuántos faltan por leer y cuántos están observados.

- **Criterios de Aceptación:**
  - Indicadores clave:
    - Total de medidores activos en servicio.
    - Lecturas registradas (% de avance).
    - Lecturas pendientes de toma.
    - Lecturas observadas sin resolver.
    - Obligaciones emitidas (monto total devengado en Bs).

---

## 4. Requisitos Funcionales (FR)

- **FR-001 (Periodo Mensual):** El sistema debe gestionar periodos en formato canónico `YYYY-MM` (ej. `2026-10`).
- **FR-002 (Modelo Lectura):** Debe registrar `medidor`, `socio`, `periodo`, `lectura_anterior`, `lectura_actual`, `consumo_m3`, `fecha_lectura`, `estado` y `observaciones`.
- **FR-003 (Lectura Anterior Determinística):** El sistema debe calcular automáticamente la lectura anterior buscando la lectura válida más reciente del medidor, o la `lectura_instalacion` si es el primer periodo.
- **FR-004 (Cálculo Inmediato):** El sistema debe computar $\text{Consumo} = \text{Lectura Actual} - \text{Lectura Anterior}$.
- **FR-005 (Validación Monotónica R-DOM-07):** Si `lectura_actual < lectura_anterior`, el sistema debe asignar automáticamente el estado `OBSERVADA`.
- **FR-006 (Bloqueo Facturación P10):** Las lecturas `OBSERVADA` o `ANULADA` no pueden generar obligaciones de pago.
- **FR-007 (Unicidad R-DOM-08):** Restricción única en base de datos para `(medidor, periodo)` sobre lecturas válidas/activas.
- **FR-008 (Auditoría de Corrección P5, P6):** Toda modificación a una lectura debe guardar el historial en `BitacoraAuditoria`.
- **FR-009 (Proforma Informativa R-DOM-09):** Generación de constancia de lectura imprimible/digital con leyenda explícita de no-recibo.
- **FR-010 (Historial de 3 Meses en Proforma):** Mostrar hasta 3 periodos previos reales disponibles sin inventar datos.
- **FR-011 (Motor de Facturación):** Proceso batch o individual que transforma lecturas validadas en obligaciones de cobro.
- **FR-012 (Resolución Tarifaria R-DOM-10):** Aplicación estricta del tarifario vigente a la fecha del periodo.
- **FR-013 (Snapshot R-DOM-11):** Almacenar en la obligación el desglose exacto de tramos, tarifas y metros cúbicos aplicados.
- **FR-014 (Idempotencia R-DOM-12):** La ejecución repetida del motor de facturación no duplica obligaciones.
- **FR-015 (Vencimiento R-DOM-14):** Fecha de vencimiento fijada al día institucional configurado o último día del mes.
- **FR-016 (Bandeja de Observadas):** Vista para listar, filtrar y resolver lecturas observadas con supervisor autorizado.
- **FR-017 (Reinicio de Contador / Rollover):** Flujo especial documentado para medidores con vuelta a cero.
- **FR-018 (Permisos RBAC):** Endpoints protegidos con `LECTURAS:VER`, `LECTURAS:CREAR`, `LECTURAS:MODIFICAR`, `CONSUMO:GENERAR`.

---

## 5. Requisitos No Funcionales (NFR)

- **NFR-001 (Precisión Numérica):** Lecturas y consumos en `DECIMAL(10,2)` y montos en `DECIMAL(12,2)`.
- **NFR-002 (Transaccionalidad ACID):** Emisión de obligaciones por lote envuelta en transacciones atómicas con rollback ante inconsistencias.
- **NFR-003 (Rendimiento en Batch):** Facturación de 1,000 lecturas en menos de 3 segundos en base de datos relacional.
- **NFR-004 (Mobile-Friendly):** Formulario de captura adaptado a pantallas táctiles para toma de lectura en campo.

---

## 6. Criterios de Éxito (SC)

- **SC-001:** Se registra la lectura de un periodo y el sistema calcula automáticamente el consumo correcto.
- **SC-002:** Se ingresa una lectura menor a la anterior y el sistema la marca como `OBSERVADA`, impidiendo su facturación.
- **SC-003:** Se emite la proforma informativa mostrando hasta 3 lecturas anteriores reales con la leyenda de no-recibo.
- **SC-004:** Se ejecuta el motor de facturación y se generan las obligaciones con su desglose snapshot correspondiente.
- **SC-005:** Se reejecuta la facturación del mismo periodo y se verifica idempotencia al 100% (cero duplicados).
- **SC-006:** Suite completa de pruebas automatizadas aprobada al 100% con `pytest`.

