---
description: "Task list for Feature 001 - Configuración Institucional, Roles, Permisos y Seguridad"
---

# Tasks: 001-configuracion-seguridad

**Input**: Design documents from `/specs/001-configuracion-seguridad/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`)  
**Prerequisites**: Python 3.12+ / Django 5.x / PostgreSQL 16+  
**Format**: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto Django, configuración de dependencias y estructura modular.

- [x] T001 Inicializar el proyecto Django y crear la estructura de carpetas (`config/`, `apps/core/`, `apps/seguridad/`, `apps/configuracion/`, `templates/`, `static/`, `tests/`).
- [x] T002 Crear y congelar `requirements.txt` con Django 5.x, psycopg (v3), argon2-cffi, pillow, pytest y pytest-django.
- [x] T003 [P] Configurar `.env.example` y `config/settings.py` con variables para PostgreSQL, secret key y configuración de cookies seguras.
- [x] T004 [P] Configurar el motor de pruebas `pytest.ini` y fixtures base en `tests/conftest.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modelos base, base de datos relacional y servicios transversales de auditoría y excepciones.

**⚠️ CRITICAL**: Ninguna historia de usuario puede arrancar hasta completar esta fase.

- [x] T005 Implementar el modelo abstracto `BaseAuditableModel` con campos `created_at`, `updated_at`, `activo` en `apps/core/models.py`.
- [x] T006 Implementar el modelo `BitacoraAuditoria` (Append-Only) en `apps/core/models.py` y registrar el trigger PostgreSQL de inmutabilidad en migraciones.
- [x] T007 Implementar el servicio unificado `registrar_auditoria()` en `apps/core/services.py` con sanitización estricta de contraseñas y secretos.
- [x] T008 [P] Configurar la lista de `PASSWORD_HASHERS` en `config/settings.py` con `Argon2PasswordHasher` en primer lugar y `BCryptSHA256PasswordHasher` como secundario.

**Checkpoint**: Base de datos y servicios transversales listos — las historias de usuario pueden comenzar.

---

## Phase 3: User Story 1 — Autenticación Segura y Forzado de Clave Temporal (Priority: P1) 🎯 MVP

**Goal**: Permitir a cualquier usuario iniciar sesión de forma segura, forzar el cambio obligatorio de clave temporal en el primer acceso (prohibiendo el CI como clave definitiva) y bloquear cuentas ante 5 intentos fallidos consecutivos.

**Independent Test**: Iniciar sesión con clave temporal, verificar redirección forzosa a `/perfil/cambiar-contrasena/`, rechazar intento de usar el CI o claves débiles, aceptar clave válida y comprobar acceso posterior.

### Tests para User Story 1
- [x] T009 [P] [US1] Pruebas unitarias de autenticación con Argon2id, cambio de clave forzado y bloqueo por intentos fallidos en `tests/test_auth.py`.

### Implementación para User Story 1
- [x] T010 [US1] Implementar el modelo `Usuario` personalizado en `apps/seguridad/models.py` con `ci_numero`, `requiere_cambio_clave`, `intentos_fallidos` y `bloqueado_hasta`.
- [x] T011 [US1] Crear el formulario `LoginForm` y `CambiarClaveForm` con validación de complejidad (8+ caracteres, alfanumérico, no igual al CI ni al username) en `apps/seguridad/forms.py`.
- [x] T012 [US1] Implementar el middleware `ForzarCambioClaveMiddleware` en `apps/core/middleware.py` que intercepta cualquier petición y redirige a cambio de clave si `requiere_cambio_clave = True`.
- [x] T013 [US1] Implementar las vistas `login_view`, `logout_view` y `cambiar_contrasena_view` en `apps/seguridad/views.py`.
- [x] T014 [US1] Crear las plantillas responsivas `templates/auth/login.html` y `templates/auth/cambiar_clave.html` con Tailwind CSS y mensajes claros.
- [x] T015 [US1] Conectar las rutas `/login/`, `/logout/` y `/perfil/cambiar-contrasena/` en `apps/seguridad/urls.py` y `config/urls.py`.

**Checkpoint**: User Story 1 es un incremento funcional MVP completamente operable y verificable.

---

## Phase 4: User Story 2 — Parametrización Institucional Dinámica (Priority: P1)

**Goal**: Permitir al Administrador configurar en base de datos los datos del comité/cooperativa (nombre, logo, teléfonos, dirección, NIT/personería, moneda `Bs` y textos de recibos) con reflejo inmediato en pantalla.

**Independent Test**: Ingresar a `/configuracion/institucion/` como Admin, cambiar el nombre, subir un logo PNG, guardar y verificar que el navbar y pie de página de todas las pantallas muestran la nueva información.

### Tests para User Story 2
- [x] T016 [P] [US2] Pruebas de integración para consulta y actualización de la configuración institucional en `tests/test_institucion.py`.

### Implementación para User Story 2
- [x] T017 [US2] Implementar el modelo singleton `Institucion` en `apps/configuracion/models.py`.
- [x] T018 [US2] Crear el formulario `InstitucionForm` con validación de imagen (PNG/JPG < 2MB) en `apps/configuracion/forms.py`.
- [x] T019 [US2] Implementar la vista `institucion_config_view` en `apps/configuracion/views.py` con registro del cambio en la bitácora de auditoría.
- [x] T020 [US2] Crear la plantilla responsiva `templates/configuracion/institucion.html` con previsualización en vivo del logotipo.
- [x] T021 [US2] Crear el context processor `datos_institucion` en `apps/configuracion/context_processors.py` para inyectar nombre y logo en el layout global `templates/base.html`.

**Checkpoint**: La identidad visual y datos oficiales del comité son dinámicos y personalizables.

---

## Phase 5: User Story 3 — Matriz de Roles y Permisos RBAC Server-Side (Priority: P1)

**Goal**: Asignar permisos granulares por módulo y acción a cada rol y verificar obligatoriamente en el servidor cada solicitud HTTP, denegando accesos no autorizados con HTTP 403.

**Independent Test**: Asignar permisos restringidos al rol Cajero, intentar acceder por URL directa a configuración o administración de usuarios, y verificar que el servidor responde con HTTP 403 Forbidden y audita el evento.

### Tests para User Story 3
- [x] T022 [P] [US3] Pruebas de autorización RBAC server-side con peticiones autorizadas y denegadas en `tests/test_rbac.py`.

### Implementación para User Story 3
- [x] T023 [US3] Implementar los modelos `Rol`, `Permiso` y `RolPermiso` en `apps/seguridad/models.py`.
- [x] T024 [US3] Crear script de seed data `fixtures/seed_roles_permisos.json` con los roles canónicos (`ADMINISTRADOR`, `CAJERO`, `LECTOR`, `SOCIO`, `AUDITOR`) y el catálogo completo de permisos por módulo.
- [x] T025 [US3] Implementar el decorador `@requiere_permiso(modulo, accion)` y el mixin `PermisoRequeridoMixin` en `apps/core/decorators.py`.
- [x] T026 [US3] Implementar las vistas de administración de roles y asignación de matriz de permisos en `apps/seguridad/views.py`.
- [x] T027 [US3] Crear la plantilla interactiva `templates/seguridad/roles_list.html` con checkboxes por módulo y acción.

**Checkpoint**: El control de acceso está blindado del lado del servidor.

---

## Phase 6: User Story 7 — Pista de Auditoría de Seguridad Inalterable (Priority: P1)

**Goal**: Visualizar y filtrar cronológicamente la bitácora inmutable de eventos de seguridad (inicios de sesión, cambios de clave, accesos denegados, modificaciones de roles) garantizando cero contraseñas o secretos en pantalla o base de datos.

**Independent Test**: Generar 3 eventos de seguridad, ingresar como Auditor a `/auditoria/`, aplicar filtros por fecha y verificar que los detalles no contienen hashes ni credenciales en claro.

### Tests para User Story 7
- [x] T028 [P] [US7] Pruebas de inmutabilidad de la bitácora y verificación de ausencia de secretos en `tests/test_auditoria.py`.

### Implementación para User Story 7
- [x] T029 [US7] Implementar la vista `auditoria_list_view` en `apps/core/views.py` con filtros por fecha, usuario, módulo y resultado.
- [x] T030 [US7] Crear la plantilla responsiva `templates/core/auditoria_list.html` con paginación y visualización del detalle JSON estructurado.

---

## Phase 7: User Story 4 — Gestión Dinámica y Segura de Menús (Priority: P2)

**Goal**: Renderizar la barra lateral de navegación estructurada jerárquicamente y filtrada de forma automática según los permisos del usuario autenticado.

**Independent Test**: Iniciar sesión con un usuario Socio y verificar que solo aparecen sus accesos personales; iniciar sesión como Cajero y verificar que solo aparece el grupo de Caja.

### Implementación para User Story 4
- [x] T031 [US4] Implementar el modelo `Menu` en `apps/configuracion/models.py` con relaciones jerárquicas y permisos requeridos.
- [x] T032 [US4] Crear el context processor `menu_navegacion` en `apps/configuracion/context_processors.py` que construye el árbol de navegación autorizado.
- [x] T033 [US4] Actualizar `templates/base.html` con la barra lateral dinámica y responsive (con toggle móvil).
- [x] T034 [US4] Implementar la vista de reordenamiento y activación/desactivación de menús en `apps/configuracion/views.py`.

---

## Phase 8: User Story 5 — Creación y Enrolamiento de Usuarios Administrativos (Priority: P2)

**Goal**: Dar de alta al personal con sugerencia automática de username (`mlopez`), resolución de colisiones (`mlopez1`), generación de clave temporal aleatoria y ficha de entrega imprimible.

**Independent Test**: Crear al usuario "Juan Pérez", verificar sugerencia de `jperez`, confirmar alta, comprobar generación de clave temporal y emisión de talón de entrega confidencial.

### Implementación para User Story 5
- [x] T035 [US5] Implementar el servicio utilitario `sugerir_username(nombres, apellido)` en `apps/seguridad/services.py` con verificación de colisiones.
- [x] T036 [US5] Implementar la vista `usuario_crear_view` y el endpoint `/administracion/usuarios/sugerir-username/` en `apps/seguridad/views.py`.
- [x] T037 [US5] Crear la plantilla `templates/seguridad/usuarios_list.html` con formulario modal de alta y botón de talón de entrega.
- [x] T038 [US5] Diseñar la plantilla de impresión de ficha confidencial `templates/seguridad/ficha_enrolamiento.html`.

---

## Phase 9: User Story 6 — Autoservicio de Perfil de Usuario (Priority: P3)

**Goal**: Permitir al usuario consultar sus datos personales, actualizar su teléfono, subir su fotografía de perfil y cambiar voluntariamente su contraseña.

**Independent Test**: Ingresar a `/perfil/`, cambiar contraseña validando la anterior, actualizar foto JPG y verificar persistencia.

### Implementación para User Story 6
- [x] T039 [US6] Implementar el formulario `PerfilForm` en `apps/seguridad/forms.py` con validación de imagen.
- [x] T040 [US6] Implementar la vista `perfil_view` en `apps/seguridad/views.py`.
- [x] T041 [US6] Crear la plantilla `templates/seguridad/perfil.html` con pestañas de Datos Personales y Seguridad.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Verificación integral, documentación y validación de calidad.

- [x] T042 [P] Ejecutar la suite completa de pruebas unitarias y de integración (`pytest -v`) asegurando 100% de tests en verde (20/20 tests aprobados).
- [x] T043 Ejecutar el checklist de verificación en vivo siguiendo `quickstart.md` (Self-Test E2E).
- [x] T044 [P] Actualizar `CLAUDE.md` y registrar el cierre de la Fase 1 en la bitácora de features.
