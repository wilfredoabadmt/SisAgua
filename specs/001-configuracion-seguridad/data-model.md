# Data Model: Fase 1 — Configuración Institucional, Roles, Permisos y Seguridad

**Feature**: `001-configuracion-seguridad`  
**Phase**: Phase 1 (Data Architecture & Schema Design)  
**Status**: Ready for Implementation  
**Motor de Persistencia**: PostgreSQL 16+ con cumplimiento ACID  
**Directriz Constitucional**: Prohibición de DELETE físico (P5), Tipos monetarios exactos (P8), Cero secretos en texto plano (P7).

---

## 1. Esquema Relacional de Entidades

```mermaid
erDiagram
    institucion {
        int id PK
        varchar(150) nombre
        varchar(255) logo_url
        text direccion
        varchar(50) telefono
        varchar(50) nit_personeria
        varchar(10) moneda
        text texto_recibo
        timestamptz created_at
        timestamptz updated_at
        boolean activo
    }

    rol {
        int id PK
        varchar(50) codigo UK
        varchar(100) nombre
        text descripcion
        boolean es_sistema
        boolean activo
        timestamptz created_at
        timestamptz updated_at
    }

    permiso {
        int id PK
        varchar(50) modulo
        varchar(50) accion
        varchar(150) descripcion
        UK modulo_accion
    }

    rol_permiso {
        int id PK
        int rol_id FK
        int permiso_id FK
        UK rol_permiso_unique
    }

    usuario {
        int id PK
        varchar(50) username UK
        varchar(255) password_hash
        varchar(100) nombres
        varchar(100) apellido_paterno
        varchar(100) apellido_materno
        varchar(30) ci_numero
        varchar(10) ci_expedido
        varchar(100) email
        varchar(50) telefono
        varchar(255) foto_perfil_url
        int rol_id FK
        boolean requiere_cambio_clave
        int intentos_fallidos
        timestamptz bloqueado_hasta
        timestamptz ultimo_acceso
        boolean activo
        timestamptz created_at
        timestamptz updated_at
    }

    menu {
        int id PK
        varchar(100) titulo
        varchar(200) ruta
        varchar(50) icono
        int orden
        int padre_id FK "nullable"
        int permiso_requerido_id FK "nullable"
        boolean activo
        timestamptz created_at
    }

    bitacora_auditoria {
        bigint id PK
        timestamptz fecha_hora_utc
        int usuario_id FK "nullable"
        varchar(45) ip_origen
        varchar(50) modulo
        varchar(50) accion
        varchar(20) resultado
        varchar(100) entidad_afectada
        varchar(50) registro_id
        jsonb detalle_json
    }

    rol ||--o{ usuario : "asigna"
    rol ||--|{ rol_permiso : "posee"
    permiso ||--|{ rol_permiso : "vinculado"
    menu ||--o{ menu : "submenus"
    permiso ||--o{ menu : "controla_visibilidad"
    usuario ||--o{ bitacora_auditoria : "audita"
```

---

## 2. Definición Detallada de Modelos Django

### 2.1. Modelo `Institucion` (Singleton de Configuración)
Representa los parámetros institucionales del comité o cooperativa de agua potable.
*   `id`: `BigAutoField`, Primary Key.
*   `nombre`: `CharField(max_length=150)` — Nombre oficial de la organización (ej. "Comité de Agua Potable San Miguel").
*   `logo`: `ImageField(upload_to='institucion/logos/', null=True, blank=True)` — Logotipo oficial.
*   `direccion`: `TextField(blank=True)` — Dirección física de la sede o zona de operación.
*   `telefono`: `CharField(max_length=50, blank=True)` — Teléfonos de contacto o celular de emergencia de la red.
*   `nit_personeria`: `CharField(max_length=50, blank=True)` — NIT o número de personería jurídica comunitaria.
*   `moneda`: `CharField(max_length=10, default='Bs')` — Moneda oficial (por defecto bolivianos).
*   `texto_recibo`: `TextField(blank=True)` — Mensaje o pie de página institucional para recibos oficiales.
*   `dia_facturacion`: `PositiveSmallIntegerField(default=1)` — Día base para corte y facturación.
*   `dia_vencimiento_default`: `PositiveSmallIntegerField(default=15)` — Día sugerido de vencimiento de obligaciones.
*   `activo`: `BooleanField(default=True)` — Banderas de estado lógico.
*   *Restricción:* Únicamente puede existir un registro activo a la vez (Singleton Pattern a nivel de aplicación).

### 2.2. Modelo `Rol`
Define los perfiles de acceso en el sistema.
*   `id`: `BigAutoField`, Primary Key.
*   `codigo`: `CharField(max_length=50, unique=True)` — Slug identificador único (`ADMINISTRADOR`, `CAJERO`, `LECTOR`, `SOCIO`, etc.).
*   `nombre`: `CharField(max_length=100)` — Nombre legible para interfaz.
*   `descripcion`: `TextField(blank=True)` — Detalle de funciones y alcance del rol.
*   `es_sistema`: `BooleanField(default=False)` — Si es `True`, el rol no puede ser eliminado ni desactivado (roles canónicos).
*   `activo`: `BooleanField(default=True)` — Borrado lógico.

### 2.3. Modelo `Permiso` y `RolPermiso`
Matriz granular de control de accesos.
*   `modulo`: `CharField(max_length=50)` — Código del módulo (`institucion`, `usuarios`, `roles`, `menus`, `socios`, `medidores`, `lecturas`, `consumo`, `caja`, `transcripcion`, `reportes`, `portal`).
*   `accion`: `CharField(max_length=50)` — Acción permitida (`ver`, `crear`, `modificar`, `anular`, `imprimir`, `exportar`, `aprobar`, `validar`, `migrar`).
*   `descripcion`: `CharField(max_length=150)` — Explicación del permiso.
*   *Restricción de Unicidad:* `unique_together = ('modulo', 'accion')`.

### 2.4. Modelo `Usuario` (Custom User Model)
Extiende `AbstractBaseUser` y `PermissionsMixin` de Django.
*   `username`: `CharField(max_length=50, unique=True, db_index=True)` — Identificador único (`mlopez`).
*   `password`: `CharField(max_length=255)` — Hash criptográfico Argon2id.
*   `nombres`: `CharField(max_length=100)` — Nombres de la persona.
*   `apellido_paterno`: `CharField(max_length=100)` — Primer apellido.
*   `apellido_materno`: `CharField(max_length=100, blank=True)` — Segundo apellido.
*   `ci_numero`: `CharField(max_length=30, blank=True, db_index=True)` — Número de Documento de Identidad.
*   `ci_expedido`: `CharField(max_length=10, blank=True)` — Departamento de expedición (`LP`, `CB`, `SC`, etc.).
*   `email`: `EmailField(max_length=100, blank=True)` — Correo electrónico de contacto (opcional para el socio).
*   `telefono`: `CharField(max_length=50, blank=True)` — Celular o teléfono para avisos.
*   `foto_perfil`: `ImageField(upload_to='usuarios/fotos/', null=True, blank=True)`.
*   `rol`: `ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios')` — Rol asignado.
*   `requiere_cambio_clave`: `BooleanField(default=True)` — Si es `True`, el middleware bloquea cualquier navegación hasta que el usuario cambie su contraseña en `/perfil/cambiar-contrasena`.
*   `intentos_fallidos`: `PositiveSmallIntegerField(default=0)` — Contador de fallos consecutivos de login.
*   `bloqueado_hasta`: `DateTimeField(null=True, blank=True)` — Marca temporal de bloqueo por fuerza bruta.
*   `activo`: `BooleanField(default=True)` — Estado de la cuenta.

### 2.5. Modelo `Menu`
Árbol jerárquico de navegación lateral y superior.
*   `id`: `BigAutoField`, Primary Key.
*   `titulo`: `CharField(max_length=100)` — Texto a mostrar en el menú.
*   `ruta`: `CharField(max_length=200)` — URL name de Django (ej. `institucion:configuracion`).
*   `icono`: `CharField(max_length=50, blank=True)` — Identificador del icono (Heroicons / Lucide).
*   `orden`: `PositiveSmallIntegerField(default=0)` — Posición relativa de renderizado.
*   `padre`: `ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='hijos')` — Submenú.
*   `permiso_requerido`: `ForeignKey(Permiso, null=True, blank=True, on_delete=models.SET_NULL)` — Permiso mínimo necesario para visibilidad.
*   `activo`: `BooleanField(default=True)`.

### 2.6. Modelo `BitacoraAuditoria` (Append-Only)
Registro histórico inmutable de auditoría.
*   `id`: `BigAutoField`, Primary Key.
*   `fecha_hora_utc`: `DateTimeField(auto_now_add=True, db_index=True)` — Timestamp oficial.
*   `usuario`: `ForeignKey(Usuario, null=True, on_delete=models.SET_NULL, related_name='auditorias')` — Operador responsable.
*   `ip_origen`: `GenericIPAddressField(null=True, blank=True)` — Dirección IP del cliente.
*   `modulo`: `CharField(max_length=50, db_index=True)` — Módulo afectado.
*   `accion`: `CharField(max_length=50)` — `LOGIN`, `LOGOUT`, `CREATE`, `UPDATE`, `DELETE_LOGICO`, `AUTH_FAILED`, `ACCESS_DENIED`.
*   `resultado`: `CharField(max_length=20)` — `EXITO` o `FALLO`.
*   `entidad_afectada`: `CharField(max_length=100, blank=True)`.
*   `registro_id`: `CharField(max_length=50, blank=True)`.
*   `detalle_json`: `JSONField(default=dict, blank=True)` — Datos serializados limpios (valores anteriores y nuevos, sin secretos).

---

## 3. Directivas de Migración y Restricciones a Nivel de Base de Datos

1.  **Regla PostgreSQL Inmutable para Auditoría:**
    ```sql
    -- Prohibición de UPDATE y DELETE en bitacora_auditoria
    CREATE OR REPLACE FUNCTION denegar_modificacion_auditoria()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Operación denegada: Los registros de la bitácora de auditoría son inmutables e indestructibles.';
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trigger_proteger_auditoria
    BEFORE UPDATE OR DELETE ON bitacora_auditoria
    FOR EACH ROW EXECUTE FUNCTION denegar_modificacion_auditoria();
    ```
2.  **Índices para Rendimiento:**
    *   `idx_usuario_username`: B-Tree en `usuario(username)`.
    *   `idx_usuario_ci`: B-Tree en `usuario(ci_numero)`.
    *   `idx_auditoria_fecha_modulo`: B-Tree compuesto en `bitacora_auditoria(fecha_hora_utc, modulo)`.
    *   `idx_rol_permiso`: Unicidad en `rol_permiso(rol_id, permiso_id)`.

