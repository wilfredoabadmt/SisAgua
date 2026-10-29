# Tareas de Implementación: Fase 5 - Transcripción Histórica y Regularización (005-transcripcion-historica-regularizacion)

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En progreso
- `[x]` Completada

---

## Tareas de Implementación

### Fase 5.1: Modelos y Base de Datos
- [x] **T001**: Crear la app Django `apps/transcripcion` con su configuración y registrarla en `config/settings.py`.
- [x] **T002**: Implementar los modelos `LoteTranscripcion` y `TranscripcionLectura` en `apps/transcripcion/models.py` con protección de borrado físico (`DELETE` prohibido P5).
- [x] **T003**: Generar y aplicar las migraciones de base de datos para la aplicación `transcripcion`.

### Fase 5.2: Capa de Servicios de Negocio (Lógica Transaccional)
- [x] **T004**: Implementar servicios de creación de lote y digitación de registros (`crear_lote_transcripcion`, `transcribir_lectura`) en `apps/transcripcion/services.py`.
- [x] **T005**: Implementar máquina de estados y transiciones (`validar_transcripcion`, `observar_transcripcion`, `rechazar_transcripcion`) en `apps/transcripcion/services.py`.
- [x] **T006**: Implementar servicio de regularización de deuda histórica `regularizar_deuda_historica()` con generación atómica de `Obligacion` y trazabilidad R-DOM-19 en `apps/transcripcion/services.py`.
- [x] **T007**: Implementar función de cálculo de métricas de avance y reporte `calcular_metricas_lote()` en `apps/transcripcion/services.py`.

### Fase 5.3: Pruebas Automatizadas (TDD)
- [x] **T008**: Actualizar fixtures en `tests/conftest.py` con permisos de transcripción (`TRANSCRIPCION:VER`, `TRANSCRIPCION:CREAR`, `TRANSCRIPCION:VALIDAR`).
- [x] **T009**: Implementar pruebas unitarias y de integración para transcripción, monotonicidad histórica, cálculo de consumo y protección P5 en `tests/test_transcripcion.py`.
- [x] **T010**: Implementar pruebas para regla R-DOM-18 (no deuda automática), regla R-DOM-19 (regularización trazable a `Obligacion`), e idempotencia en `tests/test_regularizacion_deudas.py`.
- [x] **T011**: Ejecutar `pytest` y verificar aprobación de los tests de servicios de transcripción y regularización.

### Fase 5.4: Interfaz de Usuario y Vistas
- [x] **T012**: Implementar formularios en `apps/transcripcion/forms.py` (`LoteTranscripcionForm`, `TranscripcionLecturaForm`, `ObservarTranscripcionForm`, `RechazarTranscripcionForm`, `RegularizarDeudaForm`).
- [x] **T013**: Implementar vistas basadas en funciones con decoradores RBAC en `apps/transcripcion/views.py`.
- [x] **T014**: Crear plantillas HTML en `templates/transcripcion/` (`lotes_list.html`, `lote_detalle.html`, `lote_form.html`, `captura_form.html`, `reporte_transcripcion.html`).

### Fase 5.5: Rutas, Permisos y Navegación
- [x] **T015**: Configurar `apps/transcripcion/urls.py` y vincular en `config/urls.py`.
- [x] **T016**: Actualizar `fixtures/seed_menus.json` para incorporar los accesos a Lotes de Transcripción y Reporte de Migración en el menú de navegación institucional.
- [x] **T017**: Ejecutar la suite completa de pruebas de regresión (`pytest tests/`) y verificar 100% PASS (90/90 tests).
- [x] **T018**: Actualizar `CLAUDE.md` con el estado completado de la Fase 5.
