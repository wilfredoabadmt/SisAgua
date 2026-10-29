# Tareas de Implementación: Fase 6 - Reportes Administrativos (006-reportes-administrativos-financieros)

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En progreso
- `[x]` Completada

---

## Tareas de Implementación

### Fase 6.1: Estructura Base y Capa de Servicios
- [x] **T001**: Crear la app Django `apps/reportes` con su configuración y registrarla en `config/settings.py`.
- [x] **T002**: Implementar servicio analítico de deudores `obtener_reporte_deudores()` con desglose por concepto y antigüedad en `apps/reportes/services.py`.
- [x] **T003**: Implementar servicio analítico de recaudación `obtener_reporte_recaudacion()` por medio de pago y discriminación de recibos anulados en `apps/reportes/services.py`.
- [x] **T004**: Implementar servicios analíticos de consumo `obtener_reporte_consumo()`, comparativa por zona `obtener_reporte_zonas()` y membresías `obtener_reporte_membresias()` en `apps/reportes/services.py`.
- [x] **T005**: Implementar servicio de estado de cuenta individual 360° `obtener_estado_cuenta_socio()` en `apps/reportes/services.py`.

### Fase 6.2: Pruebas Automatizadas (TDD)
- [x] **T006**: Actualizar fixtures en `tests/conftest.py` con permisos de reportes (`REPORTES:VER`, `REPORTES:EXPORTAR`).
- [x] **T007**: Implementar pruebas para cálculo de deudores, sumas no duplicadas, exclusión de pagados y antigüedad en `tests/test_reportes_deudores.py`.
- [x] **T008**: Implementar pruebas para conciliación de recaudación neta, medios de pago y recibos anulados en `tests/test_reportes_recaudacion.py`.
- [x] **T009**: Implementar pruebas para vistas web de reportes y exportación CSV en `tests/test_reportes_views.py`.
- [x] **T010**: Ejecutar `pytest` y verificar aprobación de todos los tests de reportes.

### Fase 6.3: Interfaz de Usuario y Vistas
- [x] **T011**: Implementar vistas basadas en funciones con decoradores RBAC y generador de CSV en `apps/reportes/views.py`.
- [x] **T012**: Crear plantillas HTML en `templates/reportes/`:
  - `dashboard.html`: Panel ejecutivo central.
  - `deudores.html`: Reporte de deudores con filtros e impresión.
  - `recaudacion.html`: Reporte de recaudación por medio de pago.
  - `consumo.html`: Reporte de consumo volumétrico y anomalías.
  - `zonas.html`: Balance territorial por zona.
  - `membresias.html`: Reporte de estado de afiliaciones.
  - `socio_estado_cuenta.html`: Estado de cuenta individual 360°.

### Fase 6.4: Rutas, Permisos y Navegación
- [x] **T013**: Configurar `apps/reportes/urls.py` y vincular en `config/urls.py`.
- [x] **T014**: Actualizar `fixtures/seed_menus.json` para incorporar los accesos a Reporte de Deudores, Recaudación, Consumo y Zonas en el menú de navegación institucional.
- [x] **T015**: Ejecutar la suite completa de pruebas de regresión (`pytest tests/`) y verificar 100% PASS.
- [x] **T016**: Actualizar `CLAUDE.md` con el estado completado de la Fase 6.
