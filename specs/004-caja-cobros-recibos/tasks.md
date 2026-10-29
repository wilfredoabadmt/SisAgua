# Tareas de Implementación: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En progreso
- `[x]` Completada

---

## Tareas de Implementación

### Fase 4.1: Modelos y Base de Datos
- [x] **T001**: Crear la app Django `apps/caja` con su configuración y registrarla en `config/settings.py`.
- [x] **T002**: Implementar los modelos `CajaTurno`, `Recibo`, `DetalleRecibo` y `Pago` en `apps/caja/models.py` con protección de borrado físico (`DELETE` prohibido P5).
- [x] **T003**: Generar y aplicar las migraciones de base de datos para la aplicación `caja`.

### Fase 4.2: Capa de Servicios de Negocio (Lógica Transaccional)
- [x] **T004**: Implementar conversor de números a literal en bolivianos (ej. `monto_a_literal()`) y generador de hash/código de verificación en `apps/caja/utils.py`.
- [x] **T005**: Implementar servicios de gestión de turnos (`iniciar_turno_caja`, `cerrar_turno_caja`) en `apps/caja/services.py`.
- [x] **T006**: Implementar servicio transaccional de cobro multiconcepto `procesar_cobro()` con `select_for_update()`, validación R-DOM-15, emisión correlativa R-DOM-16/17 y auditoría P6 en `apps/caja/services.py`.
- [x] **T007**: Implementar servicio de anulación autorizada `anular_recibo()` con reversión de obligaciones a `PENDIENTE` y auditoría en `apps/caja/services.py`.

### Fase 4.3: Pruebas Automatizadas (TDD)
- [x] **T008**: Actualizar fixtures en `tests/conftest.py` con permisos de caja (`CAJA:VER`, `CAJA:CREAR`, `CAJA:CERRAR`, `CAJA:ANULAR`).
- [x] **T009**: Implementar pruebas unitarias y de integración para cobro, bloqueo concurrente, regla R-DOM-15, emisión inalterable y anulación autorizada en `tests/test_caja_cobros.py`.
- [x] **T010**: Implementar pruebas para apertura de turno, cobro asociado, cálculo de arqueo por método de pago, diferencias y cierre en `tests/test_caja_turnos.py`.
- [x] **T011**: Ejecutar `pytest` y verificar aprobación total de los tests de servicios.

### Fase 4.4: Interfaz de Usuario y Vistas
- [x] **T012**: Implementar formularios en `apps/caja/forms.py` (`AperturaTurnoForm`, `CierreTurnoForm`, `CobroVentanillaForm`, `AnularReciboForm`).
- [x] **T013**: Implementar vistas basadas en funciones con decoradores RBAC en `apps/caja/views.py`.
- [x] **T014**: Crear plantillas HTML en `templates/caja/` (`cobros.html`, `recibo_detalle.html`, `recibos_list.html`, `turno_apertura.html`, `turno_cierre.html`, `turnos_list.html`).

### Fase 4.5: Rutas, Permisos y Navegación
- [x] **T015**: Configurar `apps/caja/urls.py` y vincular en `config/urls.py`.
- [x] **T016**: Actualizar `fixtures/seed_menus.json` para incorporar los accesos a Ventanilla de Cobro, Recibos y Turnos de Caja en el menú de navegación institucional.
- [x] **T017**: Ejecutar la suite completa de pruebas de regresión (`pytest tests/`) y verificar 100% PASS (75/75 tests).
- [x] **T018**: Actualizar `CLAUDE.md` con el estado completado de la Fase 4.
