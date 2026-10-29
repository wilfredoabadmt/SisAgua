# Decisiones de Diseño y Arquitectura: Fase 5 - Transcripción Histórica y Regularización (005-transcripcion-historica-regularizacion)

## 1. Justificación y Contexto
La migración de datos desde planillas manuscritas y cuadernos comunitarios es una etapa crítica en la adopción de SisAgua. La Sección 8 de la fuente funcional y la Constitución SDD v1.0 exigen rigurosidad para no contaminar la contabilidad con datos informativos dudosos y asegurar trazabilidad absoluta de las deudas regularizadas.

---

## 2. Registro de Decisiones de Arquitectura (ADR)

### DEC-028: Creación de la Aplicación `apps/transcripcion`
- **Contexto**: Se requiere un subsistema dedicado a la gestión de lotes físicos, transcripción, bandejas de validación y regularización, sin sobrecargar `apps/consumo` o `apps/servicios`.
- **Decisión**: Crear la aplicación `apps.transcripcion` conteniendo:
  - `LoteTranscripcion`: Representa la unidad documental física (cuaderno, empadronamiento o planilla Excel).
  - `TranscripcionLectura`: Registro individual de lectura y deuda histórica.
- **Consecuencias**: Clara separación de responsabilidades (P14), manteniendo un ciclo de vida propio antes de la integración contable.

---

### DEC-029: Máquina de Estados Finita para Registros Históricos
- **Contexto**: La sección 8.3 de la fuente impone al menos 6 estados: `PENDIENTE`, `TRANSCRITO`, `OBSERVADO`, `VALIDADO`, `MIGRADO`, `RECHAZADO`.
- **Decisión**: Implementar validaciones de transición en los métodos de servicio:
  - Solo registros `TRANSCRITO` u `OBSERVADO` pueden pasar a `VALIDADO`.
  - Solo registros `VALIDADO` pueden pasar a `MIGRADO` (mediante migración de lectura o regularización de deuda).
  - Registros con inconsistencias o datos dudosos pasan a `OBSERVADO`.
  - Registros no utilizables pasan a `RECHAZADO` con motivo documentado.
  - Toda transición registra usuario, fecha y auditoría (P6).
- **Consecuencias**: Control total del flujo de migración y prevención de saltos de etapa no autorizados.

---

### DEC-030: Desacoplamiento de Lecturas Históricas y Cuentas por Cobrar (R-DOM-18)
- **Contexto**: En muchos comités de agua, las lecturas antiguas son útiles para análisis de consumo y proformas, pero no necesariamente representan deudas impagas.
- **Decisión**:
  - Al transcribir y validar una lectura histórica, esta se almacena exclusivamente en `TranscripcionLectura`.
  - No se crea ninguna fila en `servicios.Obligacion` de forma automática.
  - La cuenta corriente del socio y la ventanilla de caja no muestran ninguna deuda originada por transcripción hasta que exista una acción explícita de regularización.
- **Consecuencias**: Cumplimiento estricto de la regla R-DOM-18 y prevención de cobros indebidos a socios.

---

### DEC-031: Motor de Regularización Trazable de Deudas Históricas (R-DOM-19)
- **Contexto**: Cuando una deuda antigua sí está impaga y respaldada por actas o asamblea, debe ser incorporada para su cobro oficial en ventanilla de caja.
- **Decisión**:
  - El servicio `regularizar_deuda_historica(transcripcion, usuario_autorizador, motivo_respaldo, ip)`:
    1. Valida que el registro esté en estado `VALIDADO`.
    2. Valida que exista un importe documentado o calculado mayor a cero.
    3. Verifica que no exista una `Obligacion` previa para ese socio, servicio y periodo.
    4. Crea dentro de una transacción ACID la `Obligacion` en estado `PENDIENTE`.
    5. Actualiza el registro de transcripción a estado `MIGRADO`, vinculando la FK `obligacion_regularizada`.
    6. Registra la auditoría completa en `BitacoraAuditoria`.
- **Consecuencias**: Las deudas regularizadas pueden ser cobradas en caja emitiendo su respectivo recibo oficial (R-DOM-16/17), manteniendo el vínculo inquebrantable con la planilla física original.

---

### DEC-032: Transparencia en Importes: Documentado vs Calculado (P8)
- **Contexto**: Un cuaderno físico de 2023 puede tener anotado un importe de Bs 20.00, mientras que el tarifario actual del sistema calcularía Bs 25.00.
- **Decisión**:
  - `importe_documentado`: El monto histórico textual que figura en el documento físico.
  - `importe_calculado`: El monto resultante de aplicar la tarifa conocida al consumo calculado.
  - El sistema muestra ambos campos por separado, evitando suposiciones o sobreescrituras arbitrarias.
- **Consecuencias**: Transparencia contable absoluta y apego a la realidad documental.

---

### DEC-033: Prohibición de Eliminación Física (Principio P5)
- **Contexto**: Errores al digitar planillas no deben borrarse físicamente de la base de datos para no perder rastro del trabajo de transcripción.
- **Decisión**:
  - Los modelos `LoteTranscripcion` y `TranscripcionLectura` sobreescriben `delete()` para lanzar `ValidationError`.
  - Las transcripciones erróneas se gestionan mediante el estado `RECHAZADO` o corrección autorizada.
- **Consecuencias**: Integridad histórica y cumplimiento normativo.

