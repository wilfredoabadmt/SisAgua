# Plan de Implementación: Fase 7 - Portal Individual de Socios (007-portal-individual-socios)

## 1. Objetivos del Plan
Implementar el portal individual de autoservicio para socios comunitarios conforme a la Sección 11 de la fuente funcional y directrices de la AAPS, garantizando aislamiento estricto de identidad, consulta de consumos, deudas, recibos oficiales y proformas sin valor fiscal.

## 2. Fases de Ejecución

### Fase 7.1: Modelo y Servicios de Habilitación de Cuenta
- Extender `Socio` con campo `usuario` (`OneToOneField` a `seguridad.Usuario`).
- Migración de base de datos (`makemigrations socios`, `migrate`).
- Servicio `habilitar_acceso_portal(socio_id, creado_por)` en `apps/socios/services.py`:
  - Genera username único derivado del nombre y apellido (`mlopez` o `mlopez1`).
  - Genera contraseña temporal criptográfica.
  - Asigna rol `SOCIO` con permiso `PORTAL:VER`.
  - Vincula la cuenta con `Socio.usuario`.
  - Registra auditoría.

### Fase 7.2: Creación de la App `apps/portal` y Vistas
- Crear app `apps/portal` y registrarla en `config/settings.py`.
- Implementar vistas:
  - `portal_dashboard`: Resumen integral del socio autenticado.
  - `portal_medidores`: Lecturas históricas y medidores.
  - `portal_deudas`: Cuentas pendientes y discriminación de vencimiento.
  - `portal_recibos`: Comprobantes pagados.
  - `portal_recibo_detalle`: Vista imprimible de recibo individual protegido.
  - `portal_proforma`: Vista de proforma informativa (R-DOM-09) del socio.
  - `portal_perfil`: Edición de teléfono y email.

### Fase 7.3: Plantillas Responsivas (Mobile-First)
- `templates/portal/base_portal.html`: Layout limpio adaptado a pantallas móviles y escritorio.
- `templates/portal/dashboard.html`
- `templates/portal/medidores.html`
- `templates/portal/deudas.html`
- `templates/portal/recibos.html`
- `templates/portal/recibo_detalle.html`
- `templates/portal/proforma.html`
- `templates/portal/perfil.html`

### Fase 7.4: Pruebas Automatizadas TDD
- Pruebas de habilitación de usuario de portal y generación de credenciales.
- Pruebas de acceso del socio a sus propios datos (200 OK).
- Pruebas de aislamiento estricto IDOR (404/403 al intentar acceder a recibos de otro socio).
- Pruebas de actualización de contacto y auditoría.
- Pruebas de bloqueo de operaciones administrativas desde el portal.

