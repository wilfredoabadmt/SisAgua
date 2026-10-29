# Tareas de Implementación: Fase 7 - Portal de Socios (007-portal-individual-socios)

## Leyenda de Estados
- `[ ]` Pendiente
- `[/]` En progreso
- `[x]` Completada

---

## Tareas de Implementación

### Fase 7.1: Modelo y Servicios de Credenciales
- [x] **T001**: Agregar campo `usuario` (`OneToOneField`) en el modelo `Socio` (`apps/socios/models.py`).
- [x] **T002**: Generar y aplicar migración en base de datos (`makemigrations socios`, `migrate`).
- [x] **T003**: Implementar servicio `habilitar_acceso_portal(socio_id, creado_por)` en `apps/socios/services.py` con autogeneración de usuario, contraseña temporal y rol `SOCIO`.

### Fase 7.2: App `apps/portal`, Vistas y Control de Aislamiento
- [x] **T004**: Crear la app Django `apps/portal` y registrarla en `config/settings.py` y `config/urls.py`.
- [x] **T005**: Implementar vistas seguras en `apps/portal/views.py`:
  - `portal_dashboard(request)`
  - `portal_medidores(request)`
  - `portal_deudas(request)`
  - `portal_recibos(request)`
  - `portal_recibo_detalle(request, recibo_id)` con protección anti-IDOR.
  - `portal_proforma(request, periodo)` con protección anti-IDOR.
  - `portal_perfil(request)` con formulario de actualización de datos de contacto.

### Fase 7.3: Plantillas Responsivas y Mobile-First
- [x] **T006**: Crear layout base del portal en `templates/portal/base_portal.html` con navegación adaptativa para teléfonos.
- [x] **T007**: Crear plantillas en `templates/portal/`:
  - `dashboard.html`
  - `medidores.html`
  - `deudas.html`
  - `recibos.html`
  - `recibo_detalle.html`
  - `proforma.html`
  - `perfil.html`

### Fase 7.4: Pruebas Automatizadas TDD y Verificación
- [x] **T008**: Implementar pruebas en `tests/test_portal_socios.py`:
  - Creación de cuenta y vinculación con socio.
  - Acceso de socio a su dashboard y resumen de saldo.
  - Bloqueo IDOR estricto (404/403) al intentar consultar recibos o proformas de terceros.
  - Actualización de teléfono/correo con auditoría.
  - Bloqueo de usuarios sin rol SOCIO o sin ficha de socio.
- [x] **T009**: Ejecutar la suite completa de pruebas de regresión (`pytest tests/`) y verificar 100% PASS.
- [x] **T010**: Actualizar `CLAUDE.md` con el estado completado de la Fase 7.
