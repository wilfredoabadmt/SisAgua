# Tareas de Implementación: Fase 8 - Auditoría Final y Puesta en Marcha (008-auditoria-final-puesta-en-marcha)

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En progreso
- `[x]` Completada

---

## Tareas de Implementación

### Fase 8.1: Comandos de Gestión y Diagnóstico de Salud
- [x] **T001**: Implementar comando administrativo `verificar_integridad_sistema` en `apps/core/management/commands/verificar_integridad_sistema.py` para auditar las 9 reglas de integridad de la Sección 13.
- [x] **T002**: Implementar comando de respaldo institucional `backup_institucional` en `apps/core/management/commands/backup_institucional.py` con manifiesto criptográfico SHA-256.

### Fase 8.2: Pruebas de Integración Cruzada de Fin de Ciclo
- [x] **T003**: Implementar pruebas automatizadas de integridad cruzada en `tests/test_integracion_cruzada_seccion_13.py`:
  - Detección y bloqueo de doble cobro (R-INT-06).
  - Bloqueo de doble asignación activa de medidor (R-INT-02).
  - Comprobación de sanitización de secretos en auditoría (Principio P6).
  - Ejecución del comando `verificar_integridad_sistema`.
  - Ejecución del comando `backup_institucional` y verificación de integridad del dump.
- [x] **T004**: Ejecutar la suite completa de pruebas de regresión (`pytest tests/`) y verificar 100% PASS.

### Fase 8.3: Certificación y Puesta en Marcha
- [x] **T005**: Actualizar `CLAUDE.md` con las 8 fases completadas al 100%.
- [x] **T006**: Actualizar `README.md` con la guía de arquitectura, credenciales por defecto, comandos de respaldo y estado de certificación oficial.
