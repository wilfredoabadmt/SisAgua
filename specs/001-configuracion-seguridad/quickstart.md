# Quickstart: Fase 1 — Configuración y Seguridad

**Feature**: `001-configuracion-seguridad`  
**Phase**: Phase 1 (Testing & Verification Guide)  
**Stack**: Python 3.12+ / Django 5.x / PostgreSQL 16+

---

## 1. Requisitos Previos

- Python 3.12+ instalado en el entorno (`python --version`).
- PostgreSQL 14+ corriendo localmente o en contenedor Docker.
- Entorno virtual activado.

---

## 2. Inicialización del Entorno Local

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
# En Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 2. Instalar dependencias del proyecto
pip install -r requirements.txt

# 3. Configurar variables de entorno locales (.env)
cp .env.example .env
# Configurar DATABASE_URL=postgres://usuario:password@localhost:5432/sisagua_db

# 4. Ejecutar migraciones de base de datos
python manage.py migrate

# 5. Cargar datos semilla iniciales (Roles canónicos, permisos y menús base)
python manage.py loaddata seed_roles_permisos.json
python manage.py loaddata seed_menus.json

# 6. Crear el Administrador Inicial del Sistema
python manage.py crear_admin_inicial --username=admin --ci=1234567
```

---

## 3. Verificación de Comportamiento en Vivo (Self-Test E2E)

### Escenario A: Enrolamiento y Forzado de Contraseña
1. Iniciar servidor: `python manage.py runserver`.
2. Navegar a `http://localhost:8000/login/`.
3. Ingresar con las credenciales temporales generadas para el nuevo usuario.
4. **Verificación:** El sistema bloquea el acceso al panel y redirige forzosamente a `/perfil/cambiar-contrasena/`.
5. Intentar ingresar el carnet de identidad como nueva clave: el sistema **debe rechazarlo**.
6. Ingresar una clave válida de 8+ caracteres alfanuméricos: el sistema actualiza el estado y redirige al panel correspondiente.

### Escenario B: Parametrización Institucional
1. Iniciar sesión como `admin`.
2. Acceder a `http://localhost:8000/configuracion/institucion/`.
3. Cambiar el nombre institucional a "Cooperativa de Agua San Juan" y subir un logo PNG.
4. Guardar cambios.
5. **Verificación:** El nuevo nombre y logo se reflejan instantáneamente en la barra superior y pie de página de todas las vistas.

### Escenario C: Verificación de Permisos Server-Side (RBAC)
1. Iniciar sesión como un usuario con rol `CAJERO`.
2. Intentar ingresar manualmente por barra de direcciones a `http://localhost:8000/configuracion/institucion/`.
3. **Verificación:** El servidor responde con `HTTP 403 Forbidden` y no renderiza el formulario de configuración.
4. Revisar la bitácora en `http://localhost:8000/auditoria/`: el intento de acceso no autorizado figura registrado con IP y usuario.

---

## 4. Ejecución de la Suite de Pruebas Automatizadas

```bash
# Correr todas las pruebas unitarias y de integración de la Fase 1
pytest tests/test_auth.py tests/test_institucion.py tests/test_rbac.py tests/test_auditoria.py -v

# Verificar cobertura de código (> 90% requerido)
pytest --cov=apps/seguridad --cov=apps/configuracion --cov-report=term-missing
```

