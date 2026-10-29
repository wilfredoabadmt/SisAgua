# Especificación Funcional: Fase 5 - Transcripción Histórica y Regularización de Deudas (005-transcripcion-historica-regularizacion)

## 1. Identificación y Metadatos
- **Módulo**: Grupo 8: Transcripción y migración histórica (Secciones 8.1..8.7 y 15 de la fuente funcional).
- **Ruta principal**: `/transcripcion/`
- **Estado**: Aprobado para implementación
- **Prioridad**: Crítica (Fase 5 del roadmap canónico de implementación)
- **Trazabilidad Constitucional**: P1, P2, P3, P4, P5, P6, P7, P8, P10, R-DOM-18, R-DOM-19.

---

## 2. Descripción General y Objetivos
El objetivo de este módulo es incorporar al sistema las lecturas de los socios correspondientes a meses o años anteriores, a partir de cuadernos de campo, registros manuscritos, formularios físicos y planillas Excel existentes.
Su finalidad es facilitar la migración gradual de la información sin perder el control de lo transcrito, lo pendiente y lo observado, manteniendo la estricta distinción entre el **historial de consumo estadístico** y las **deudas exigibles regularizadas** (R-DOM-18 y R-DOM-19).

### Objetivos Clave
1. Organizar la captura histórica mediante Lotes / Planillas físicas de origen (`LoteTranscripcion`).
2. Soportar el registro de lecturas anteriores, lecturas actuales, consumo calculado, importe documentado e importe calculado por tarifa histórica disponible.
3. Implementar la máquina de estados normativa (Sección 8.3): `PENDIENTE`, `TRANSCRITO`, `OBSERVADO`, `VALIDADO`, `MIGRADO`, `RECHAZADO`.
4. Garantizar la trazabilidad completa y no repudio (P6): registrar usuario transcriptor, usuario validador, fechas y justificaciones de observación o rechazo.
5. Salvaguardar la regla **R-DOM-18**: La transcripción de una lectura histórica no genera automáticamente una deuda exigible sin revisión previa.
6. Salvaguardar la regla **R-DOM-19**: Toda regularización de deuda histórica exige respaldo documental, validación formal y vínculo trazable con la `Obligacion` económica generada en el módulo de servicios para posterior cobro en caja.
7. Proveer un cuadro de mando con métricas de avance por etapa y reporte exportable (CSV / Vista de Impresión).

---

## 3. Historias de Usuario y Criterios de Aceptación (Gherkin)

### US-TRX-01: Apertura de Lote y Captura de Planillas Históricas
**Como** Responsable de Transcripción  
**Quiero** registrar un lote o cuaderno físico e ingresar fila por fila las lecturas de los socios  
**Para** digitalizar la información de meses o años anteriores con referencia al documento fuente.

#### Escenarios de Aceptación
```gherkin
Scenario: Captura exitosa de registro histórico con importe documentado
  Given que existe un lote "Cuaderno 2024 - Sector Norte" abierto
  When el transcriptor ingresa socio "SOC-0001", periodo "2024-05", lectura anterior "120", lectura actual "135", e importe documentado "30.00"
  Then el sistema calcula automáticamente el consumo histórico de 15 m³
  And guarda el registro con estado TRANSCRITO
  And registra a dicho usuario como transcriptor con marca temporal UTC
```

---

### US-TRX-02: Revisión, Observación y Validación de Transcripciones
**Como** Supervisor o Validador de Migración  
**Quiero** revisar los registros digitados, marcar observaciones o aprobarlos formalmente  
**Para** asegurar la veracidad de los datos antes de incorporarlos al historial operativo.

#### Escenarios de Aceptación
```gherkin
Scenario: Validación exitosa de registro transcrito
  Given un registro en estado TRANSCRITO
  When el supervisor ejecuta la acción de validación
  Then el estado cambia a VALIDADO
  And se registra usuario_validador y fecha_validacion
  And se audita la transición en BitacoraAuditoria

Scenario: Observación por discrepancia de lectura o datos dudosos
  Given un registro en estado TRANSCRITO con inconsistencias
  When el supervisor lo marca como OBSERVADO e ingresa "Lectura ilegible en foja 14 del cuaderno"
  Then el estado pasa a OBSERVADO y se almacena la justificación
```

---

### US-TRX-03: Distinción entre Lectura Histórica y Deuda Exigible (R-DOM-18)
**Como** Auditor y Administrador del Sistema  
**Quiero** que la transcripción de una lectura histórica no genere automáticamente una cuenta por cobrar en el estado de cuenta del socio  
**Para** no confundir datos estadísticos de consumo con deudas reales pendientes de pago.

#### Escenarios de Aceptación
```gherkin
Scenario: Registro histórico validado no altera las obligaciones de cobro
  Given que un registro de transcripción de mayo 2024 pasa a estado VALIDADO o MIGRADO a lectura
  When se consulta el estado de cuenta del socio en caja
  Then dicho registro NO aparece como obligación pendiente de cobro en ventanilla
  And el saldo adeudado del socio no se ve incrementado
```

---

### US-TRX-04: Regularización Trazable de Deuda Histórica (R-DOM-19)
**Como** Administrador o Junta Directiva  
**Quiero** regularizar expresamente una deuda histórica respaldada para incorporarla formalmente a la cuenta del socio  
**Para** que pueda ser cobrada en caja mediante la emisión de un recibo oficial con trazabilidad íntegra.

#### Escenarios de Aceptación
```gherkin
Scenario: Regularización exitosa de deuda histórica autorizada
  Given un registro de transcripción en estado VALIDADO con importe documentado de Bs 30.00
  And que no existe una obligación previa para ese socio, servicio y periodo
  When el administrador autoriza la regularización con justificación "Aprobado por Asamblea Acta Nº 45"
  Then se crea una Obligacion económica en estado PENDIENTE con monto = 30.00
  And el registro de transcripción pasa a estado MIGRADO
  And queda vinculado directamente con la Obligacion generada
  And la deuda queda disponible para cobro en ventanilla de caja

Scenario: Rechazo de regularización si ya existe obligación en ese periodo (P4 Idempotencia)
  Given un registro validado para un periodo que ya tiene una obligación registrada
  When se intenta regularizar
  Then la operación es rechazada impidiendo duplicaciones económicas
```

---

### US-TRX-05: Monitor de Avance de Migración y Reporte Exportable
**Como** Administrador y Directiva  
**Quiero** visualizar las estadísticas de avance por estado y exportar el reporte de transcripción  
**Para** auditar el progreso real de digitalización frente a los cuadernos físicos de la comunidad.

#### Escenarios de Aceptación
```gherkin
Scenario: Consulta del cuadro de mando de avance
  Given un lote con 100 registros: 40 validados, 30 migrados, 20 transcritos, 10 observados
  When se consulta el monitor de avance
  Then el sistema reporta avance de validación = 70% (validados + migrados)
  And muestra el desglose exacto por estado sin falsear porcentajes
```

---

## 4. Reglas de Negocio Protegidas
- **R-DOM-18 (Distinción entre lectura y deuda)**: Transcribir una lectura histórica no crea una obligación de cobro.
- **R-DOM-19 (Regularización trazable)**: Solo se devenga deuda con registro validado, respaldo, justificación documentada y vínculo foreign key estricto.
- **P5 (Conservación histórica)**: Prohibición absoluta de borrado físico (`DELETE` bloqueado). Registros erróneos se rechazan u observan.
- **P6 (Auditoría completa)**: Registro de transcriptor, validador, fechas y cambios de estado en `BitacoraAuditoria`.
- **P8 (Transparencia financiera)**: Distinción entre importe documentado en cuaderno e importe calculado por tarifa.

