# Plan de Implementación: Fase 8 - Auditoría Final y Puesta en Marcha (008-auditoria-final-puesta-en-marcha)

## 1. Objetivos del Plan
Consolidar el ciclo de vida completo de desarrollo (SDD) de SisAgua, implementando los comandos de integridad del sistema, respaldo y restauración institucional, auditoría exhaustiva de seguridad y la batería de pruebas de integración cruzada final (Sección 13 y 15).

## 2. Fases de Ejecución

### Fase 8.1: Comandos de Gestión Administrativa
- Implementar `python manage.py verificar_integridad_sistema` con diagnóstico de las 9 reglas de integridad de la Sección 13.
- Implementar `python manage.py backup_institucional` con checksum criptográfico SHA-256 y manifiesto de consistencia.

### Fase 8.2: Pruebas de Integración Cruzada de Fin de Ciclo (E2E)
- Crear `tests/test_integracion_cruzada_seccion_13.py` verificando:
  - Intento de doble cobro simultáneo.
  - Intento de duplicidad de asignación activa de medidor.
  - Verificación estricta de sanitización en bitácora de auditoría.
  - Verificación del comando de integridad de base de datos.
  - Verificación del comando de backup institucional y su checksum.

### Fase 8.3: Certificación y Documentación de Cierre
- Ejecutar la suite completa de pruebas de SisAgua.
- Actualizar `CLAUDE.md`, `README.md` y `tasks.md` certificando la finalización del 100% de las 8 fases canónicas.

