# Implementation Plan: Fase 1 — Configuración y Seguridad

**Branch**: `001-configuracion-seguridad` | **Date**: 28 de Octubre de 2026 | **Spec**: [specs/001-configuracion-seguridad/spec.md](spec.md)  
**Input**: Especificación funcional de la Fase 1 (Parametrización institucional, gestión de usuarios, roles y permisos RBAC, menús dinámicos, autoservicio de perfil y bitácora de auditoría inalterable).  
**Constitución Rectora**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

---

## 1. Summary

La Fase 1 establece los cimientos de gobernanza, seguridad perimetral, parametrización institucional y control de acceso del sistema SisAgua. La implementación adopta una arquitectura desacoplada basada en **Python 3.12+ y Django 5.x** con motor de base de datos relacional **PostgreSQL 16+** (confirmado bajo la Decisión Ratificada D-15). 

El sistema implementará un modelo de usuario personalizado (`Usuario`), autenticación robusta mediante **Argon2id**, forzado estricto de cambio de contraseña temporal en el primer acceso (prohibición del carnet como clave definitiva), protección contra ataques de fuerza bruta (bloqueo tras 5 intentos fallidos), matriz granular de permisos verificada obligatoriamente en el servidor (RBAC) y bitácora de auditoría inmutable (`Append-Only`) con protección a nivel de base de datos. La interfaz de usuario será 100% adaptable (*Mobile-First*) construida con Django Templates, Tailwind CSS y HTMX.

---

## 2. Technical Context

*   **Lenguaje / Versión**: Python 3.12+ (verificado en entorno: Python 3.15.1).
*   **Framework Principal**: Django 5.x (Arquitectura limpia / MVT desacoplada).
*   **Motor de Base de Datos**: PostgreSQL 16+ con adaptador `psycopg` (v3) y soporte transaccional ACID estricto.
*   **Criptografía de Contraseñas**: `argon2-cffi` (Argon2id como hasher por defecto) + `bcrypt` como respaldo.
*   **Manejo de Imágenes**: `Pillow` (para validación y redimensionamiento de logotipos y fotos de perfil).
*   **Protección de Fuerza Bruta**: Middleware personalizado de rate limiting con bloqueo temporal por 15 minutos.
*   **Testing**: `pytest` + `pytest-django` + `factory-boy` para generación de fixtures de prueba.
*   **Frontend & Estilos**: Django Templates + Tailwind CSS + HTMX (diseño responsivo sin dependencia de SPA pesada).
*   **Plataforma de Despliegue**: Servidor Linux (Ubuntu 24.04 LTS / Debian 12) sobre VPS o servidor local on-premise en sede comunitaria.
*   **Rendimiento**: Tiempo de respuesta en login y cálculo de menú dinámico $< 100\text{ ms}$.
*   **Restricciones de Seguridad**: Cero secretos en texto plano, prohibición absoluta de `DELETE` físico en auditoría y entidades maestras, protección nativa contra OWASP Top 10.

---

## 3. Constitution Check (Puerta Constitucional)

*GATE: Evaluación obligatoria previa a la fase de implementación de tareas.*

| Principio Constitucional | Estado | Justificación y Cumplimiento Técnico |
| :--- | :---: | :--- |
| **I. Seguridad y Privacidad Primero [P6, P7, P13]** | **PASS** | Hashes Argon2id; prohibición de CI como clave permanente; forzado de cambio de clave inicial; aislamiento horizontal estricto socio-socio; cero contraseñas en auditoría o logs. |
| **II. Soberanía / Self-Hosted [P11, P14]** | **PASS** | Django + PostgreSQL autoalojado sin dependencias SaaS de terceros para auth o datos. |
| **III. Aislamiento Institucional [P2, P13]** | **PASS** | Modelo `Institucion` como singleton parametrizable, preparado para evolución multi-tenant. |
| **IV. Integridad Financiera e Idempotencia [P3, P4, P8]** | **PASS** | Transacciones ACID; esquema monetario `DECIMAL(12,2)`; RBAC estricto que protege futuras rutas de caja. |
| **V. Calidad y Conservación Histórica [P5, P10]** | **PASS** | Borrado lógico con bandera `activo`; bitácora de auditoría inmutable protegida por trigger SQL; cero `DELETE` físico. |
| **VI. Specs Antes de Código [P1, P15]** | **PASS** | Especificación formal completada en `spec.md` previo a cualquier archivo de código fuente. |
| **VII. Trazabilidad de Decisiones [P6, P8]** | **PASS** | Decisión D-15 ratificada y documentada; bitácora `BitacoraAuditoria` registra operador, IP y timestamp UTC. |
| **VIII. Foco Vertical Comunitario (Bolivia)** | **PASS** | Roles canónicos adaptados a comités/cooperativas de agua (Cajero, Lector, Supervisor de Zona, Socio). |
| **IX. Verificación de Comportamiento en Vivo [P3, P12]** | **PASS** | Guía de Self-Test E2E formalizada en `quickstart.md` para verificación por el implementador. |

---

## 4. Project Structure & Layout

### 4.1. Documentación de la Feature (`specs/001-configuracion-seguridad/`)
```text
specs/001-configuracion-seguridad/
├── spec.md              # Especificación funcional observable (QUÉ y POR QUÉ)
├── plan.md              # Este documento de planificación técnica (CÓMO)
├── research.md          # Fase 0: Decisiones tecnológicas y análisis de opciones
├── data-model.md        # Fase 1: Esquema relacional, modelos Django y directivas SQL
├── quickstart.md        # Fase 1: Guía de ejecución, fixtures y self-test E2E
└── contracts/
    └── api-contracts.md # Fase 1: Contratos de endpoints, vistas, formularios y códigos HTTP
```

### 4.2. Estructura de Código Fuente Propuesta (Raíz del Proyecto)
```text
f:\Documentos\GitHub\SisAgua/
├── config/                      # Configuración global del proyecto Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Settings modular (base, local, production)
│   ├── urls.py                  # Enrutador principal de URLs
│   └── wsgi.py
├── apps/                        # Aplicaciones modulares desacopladas
│   ├── core/                    # Utilidades transversales, middleware y auditoría
│   │   ├── middleware.py        # Middleware de cambio de clave forzado y auditoría
│   │   ├── models.py            # Modelo BitacoraAuditoria y BaseModel abstracto
│   │   ├── decorators.py        # Decorador @requiere_permiso(modulo, accion)
│   │   └── services.py          # Servicio unificado de logging de auditoría
│   ├── seguridad/               # Autenticación, usuarios, roles y permisos
│   │   ├── models.py            # Usuario, Rol, Permiso, RolPermiso
│   │   ├── forms.py             # Formulario de Login, CambioClave, UsuarioForm
│   │   ├── views.py             # Vistas de Auth, Perfil, Roles y Usuarios
│   │   ├── urls.py              # Rutas de /login, /logout, /perfil, /administracion
│   │   └── services.py          # Lógica de sugerencia de username y generación de claves
│   └── configuracion/           # Parametrización institucional y menús dinámicos
│       ├── models.py            # Institucion, Menu
│       ├── forms.py             # InstitucionForm, MenuForm
│       ├── views.py             # Vistas de /configuracion/institucion y menús
│       ├── context_processors.py# Inyección del menú dinámico filtrado en plantillas
│       └── urls.py
├── templates/                   # Plantillas HTML responsivas (Tailwind CSS + HTMX)
│   ├── base.html                # Layout principal con navbar y sidebar dinámico
│   ├── auth/
│   │   ├── login.html           # Pantalla de acceso responsiva
│   │   └── cambiar_clave.html   # Pantalla de cambio obligatorio/voluntario de clave
│   ├── configuracion/
│   │   └── institucion.html     # Formulario institucional con preview de logo
│   └── seguridad/
│       ├── roles_list.html      # Matriz interactiva de roles y permisos
│       ├── usuarios_list.html   # Directorio de personal con ficha de enrolamiento
│       └── perfil.html          # Vista de autoservicio de perfil
├── static/                      # Archivos estáticos (CSS, JS, iconos)
├── tests/                       # Suite de pruebas automatizadas con pytest
│   ├── conftest.py              # Fixtures globales y clientes de prueba
│   ├── test_auth.py             # Pruebas de login, fuerza bruta y cambio de clave
│   ├── test_institucion.py      # Pruebas de parametrización institucional
│   ├── test_rbac.py             # Pruebas de verificación de permisos en servidor
│   └── test_auditoria.py        # Pruebas de inmutabilidad y protección de secretos
├── manage.py
├── requirements.txt             # Dependencias congeladas
└── .env.example                 # Variables de entorno contractuales
```

---

## 5. Complexity Tracking

*No se detectan violaciones constitucionales que requieran justificación de complejidad.*  
La arquitectura propuesta utiliza los mecanismos canónicos de Django (Modelos, Formularios, Vistas basadas en clases/funciones y Middleware) sin introducir bibliotecas externas innecesarias ni capas redundantes de microservicios en el MVP.

---

## 6. Siguiente Paso

Con el `plan.md`, `research.md`, `data-model.md` y `contracts/` listos, el flujo SDD avanza a la generación de la lista de tareas ordenadas por dependencias: **`tasks.md`**.

