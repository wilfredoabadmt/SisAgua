# Technical Research & Decisions: Fase 1 — Configuración y Seguridad

**Feature**: `001-configuracion-seguridad`  
**Phase**: Phase 0 (Research & Technical Decisions)  
**Status**: Completed  
**Date**: 28 de Octubre de 2026

---

## 1. Decisiones de Arquitectura y Stack Tecnológico

### DEC-001: Framework Backend y Versión de Lenguaje
*   **Decisión**: Python 3.12+ con Django 5.x.
*   **Fundamento**:
    1.  *Cumplimiento Constitucional (P14):* Django implementa de forma nativa el desacoplamiento MVC/MVT, separando claramente modelos, lógica de negocio y presentación.
    2.  *Seguridad por Defecto (P7):* Incorpora protección contra ataques comunes (CSRF, Clickjacking, SQL Injection mediante ORM parametrizado, XSS en plantillas).
    3.  *Panel y Autenticación Extensible:* El sistema de usuarios y permisos de Django permite extender el modelo base con un `CustomUserModel` que sustituye el email o username tradicional y añade banderas críticas (`requiere_cambio_clave`, `intentos_fallidos`).
    4.  *Soporte en Bolivia:* Facilidad de mantenimiento por desarrolladores locales y compatibilidad total con servidores Linux/VPS de bajo costo.

### DEC-002: Motor de Base de Datos y Driver
*   **Decisión**: PostgreSQL 16+ con el adaptador `psycopg` (v3).
*   **Fundamento**:
    1.  *Integridad Financiera (P3):* Soporte completo de transacciones ACID con niveles de aislamiento configurables y bloqueos pesimistas (`select_for_update()`) para operaciones de cobro y caja concurrentes.
    2.  *Restricciones de Integridad:* Integridad referencial fuerte (`ON DELETE RESTRICT` o `PROTECT`), restricciones de unicidad compuestas y tipo nativo `DECIMAL(12, 2)` para montos en bolivianos.

### DEC-003: Criptografía y Gestión de Contraseñas
*   **Decisión**: Argon2id como hasher primario (`django.contrib.auth.hashers.Argon2PasswordHasher`), con fallback a `BCryptSHA256PasswordHasher`.
*   **Fundamento**:
    1.  Argon2id es el ganador del Password Hashing Competition (PHC) y el estándar recomendado por OWASP por su resistencia contra ataques paralelos con GPU y ASIC.
    2.  Se utiliza la biblioteca estándar `argon2-cffi`.

### DEC-004: Protección contra Ataques de Fuerza Bruta (Rate Limiting)
*   **Decisión**: Middleware personalizado o integración con `django-axes` / Django Cache.
*   **Fundamento**:
    1.  *Requisito FR-004:* Bloqueo de cuenta tras 5 intentos fallidos consecutivos durante 15 minutos.
    2.  *Protección contra Enumeración:* El mensaje de error en login será siempre idéntico: *"Credenciales no válidas o cuenta temporalmente bloqueada. Por favor intente más tarde."*

### DEC-005: Control de Acceso Basado en Roles (RBAC) Server-Side
*   **Decisión**: Modelo relacional de permisos explícitos con un decorador/mixin personalizado (`@requiere_permiso(modulo, accion)`).
*   **Fundamento**:
    1.  *Requisito FR-007:* La verificación en el servidor es obligatoria para cada endpoint o vista.
    2.  Los roles estándar de Django (`Group` y `Permission`) se extienden para soportar la taxonomía del documento fuente:
        *   Módulos: `institucion`, `usuarios`, `roles`, `menus`, `zonas`, `socios`, `servicios`, `medidores`, `tarifario`, `lecturas`, `consumo`, `caja`, `transcripcion`, `reportes`, `portal`.
        *   Acciones: `ver`, `crear`, `modificar`, `anular`, `imprimir`, `exportar`, `aprobar`, `validar`, `migrar`.

### DEC-006: Bitácora de Auditoría Inalterable (Append-Only)
*   **Decisión**: Modelo `BitacoraAuditoria` gestionado mediante señales de Django (`post_save`, `post_delete`) y llamadas explícitas desde servicios de dominio.
*   **Fundamento**:
    1.  *Cumplimiento Constitucional (P6):* Registro inmutable de usuario, IP, timestamp UTC, entidad, acción y detalles en formato JSON.
    2.  *Protección de Secretos:* Limpieza estricta de payloads para asegurar que campos como `password`, `token` o `clave` jamás se persistan en la bitácora.
    3.  *Restricción en Base de Datos:* La tabla de auditoría denegará `UPDATE` y `DELETE` mediante reglas/triggers a nivel de PostgreSQL.

### DEC-007: Interfaz y Estilos Visuales
*   **Decisión**: Django Templates + Tailwind CSS (via CDN o compilado mínimo) + HTMX para interacción dinámica sin necesidad de SPA pesada.
*   **Fundamento**:
    1.  *Cumplimiento Constitucional (P12):* Interfaz 100% responsiva (Mobile-First) apta para computadoras de escritorio, tabletas y teléfonos celulares en campo.
    2.  *Bajo Consumo de Red:* Ideal para entornos con conectividad limitada en áreas periurbanas o rurales.

