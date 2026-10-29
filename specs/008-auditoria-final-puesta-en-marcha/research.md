# Investigación y Decisiones Técnicas: Fase 8 - Auditoría Final y Puesta en Marcha (008-auditoria-final-puesta-en-marcha)

## 1. Verificador Automatizado de Salud de Integridad (`verificar_integridad_sistema`)
- Implementar un comando de gestión en `apps/core/management/commands/verificar_integridad_sistema.py` que recorra sistemáticamente:
  - Consistencia de socios y membresías atómicas (R-INT-05).
  - Medidores con más de una asignación activa (R-INT-02).
  - Lecturas duplicadas por periodo (R-INT-03).
  - Obligaciones duplicadas por medidor/periodo (R-INT-04).
  - Recibos vs DetalleRecibo vs Obligaciones (conciliación contable exacta sin descalce de centavos).
  - Turnos de caja abiertos huérfanos o con arqueos inconsistentes.
  - Bitácora de auditoría: escaneo de strings para certificar ausencia de palabras clave sensibles (`password`, `argon2`, `hash`, `token`, `clave`).

## 2. Motor de Respaldos Institucionales (`backup_institucional`)
- Crear `apps/core/management/commands/backup_institucional.py`.
- Genera un archivo comprimido o estructurado en `backups/` con:
  - Dump serializado de todos los modelos de SisAgua excluyendo logs temporales.
  - Archivo de manifiesto `manifest.json` con timestamp ISO 8601, versión de SisAgua, total de registros por modelo y Hash SHA-256 para verificación de no manipulación.
  - Registro de auditoría con `modulo='SISTEMA'`, `accion='BACKUP'`.

