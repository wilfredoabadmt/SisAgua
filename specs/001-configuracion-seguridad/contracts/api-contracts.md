# API & View Contracts: Fase 1 — Configuración y Seguridad

**Feature**: `001-configuracion-seguridad`  
**Phase**: Phase 1 (Interface & Endpoint Specifications)  
**Security Baseline**: Todas las rutas mutantes (POST/PUT/PATCH/DELETE) exigen token `CSRF`. Todas las rutas protegidas exigen sesión activa y verificación de rol/permiso en el servidor.

---

## 1. Módulo de Autenticación y Credenciales

### POST `/login/`
*   **Propósito**: Autenticar usuario con username y contraseña.
*   **Acceso**: Público (con rate limiting de 5 intentos por IP/usuario en 15 min).
*   **Payload (Form / JSON)**:
    ```json
    {
      "username": "mlopez",
      "password": "TemporalPassword123"
    }
    ```
*   **Respuestas**:
    *   `200 OK` (Redirección a dashboard según rol, o a `/perfil/cambiar-contrasena/` si `requiere_cambio_clave = true`):
        ```json
        {
          "status": "success",
          "redirect_url": "/perfil/cambiar-contrasena/",
          "requiere_cambio_clave": true,
          "usuario": {
            "username": "mlopez",
            "rol": "CAJERO"
          }
        }
        ```
    *   `401 Unauthorized` (Credenciales inválidas o cuenta bloqueada):
        ```json
        {
          "status": "error",
          "message": "Credenciales no válidas o cuenta temporalmente bloqueada. Por favor intente más tarde."
        }
        ```

### POST `/logout/`
*   **Propósito**: Destruir la sesión activa y limpiar cookies de sesión en el navegador.
*   **Acceso**: Autenticado.
*   **Respuesta**: `302 Found` (Redirección a `/login/`).

### POST `/perfil/cambiar-contrasena/`
*   **Propósito**: Establecer nueva contraseña personal (forzada o voluntaria).
*   **Acceso**: Autenticado.
*   **Payload**:
    ```json
    {
      "password_actual": "TemporalPassword123",  // Opcional si es primer acceso forzado
      "password_nuevo": "NuevaClaveRobusta2026!",
      "password_confirmar": "NuevaClaveRobusta2026!"
    }
    ```
*   **Validaciones**:
    *   Mínimo 8 caracteres, al menos un número y una letra.
    *   No puede coincidir con el carnet de identidad (`ci_numero`) ni con el `username`.
    *   `password_nuevo` debe ser igual a `password_confirmar`.
*   **Respuestas**:
    *   `200 OK`: Contraseña actualizada, `requiere_cambio_clave` establecido en `false`, auditoría registrada. Redirección al dashboard.
    *   `400 Bad Request`: Mensaje con los requisitos de contraseña incumplidos.

---

## 2. Módulo de Parametrización Institucional

### GET `/configuracion/institucion/`
*   **Propósito**: Consultar datos institucionales de la entidad prestadora de agua.
*   **Permiso Requerido**: `modulo: 'institucion'`, `accion: 'ver'`.
*   **Respuesta**: `200 OK` con datos institucionales actuales.

### POST `/configuracion/institucion/`
*   **Propósito**: Actualizar los parámetros de la organización.
*   **Permiso Requerido**: `modulo: 'institucion'`, `accion: 'modificar'`.
*   **Payload (Multipart Form)**:
    *   `nombre`: "Comité de Agua Potable y Saneamiento Villa Esperanza" (String, obligatorio).
    *   `logo`: Archivo de imagen (PNG/JPG, máx 2MB, opcional).
    *   `direccion`: "Av. Principal #120, Zona Norte" (String).
    *   `telefono`: "+591 71234567" (String).
    *   `nit_personeria`: "Resolución Prefectural N° 45/2004" (String).
    *   `moneda`: "Bs" (String, solo lectura en interfaz).
    *   `texto_recibo`: "El agua es vida, cuídela. Factura sujeta a estatuto comunal." (Text).
*   **Respuestas**:
    *   `200 OK`: Configuración guardada y reflejada en el sistema; evento registrado en auditoría.
    *   `400 Bad Request`: Archivo de imagen inválido o campo obligatorio vacío.
    *   `403 Forbidden`: Usuario sin permiso administrativo.

---

## 3. Módulo de Roles y Permisos (RBAC)

### GET `/administracion/roles/`
*   **Propósito**: Listar roles activos y matriz de permisos asociados.
*   **Permiso Requerido**: `modulo: 'roles'`, `accion: 'ver'`.

### POST `/administracion/roles/crear/`
*   **Propósito**: Crear un nuevo rol con permisos seleccionados.
*   **Permiso Requerido**: `modulo: 'roles'`, `accion: 'crear'`.
*   **Payload**:
    ```json
    {
      "codigo": "SUPERVISOR_ZONA",
      "nombre": "Supervisor de Zona",
      "descripcion": "Encargado de coordinar lecturas y reclamos por zona",
      "permisos_ids": [1, 2, 5, 8, 14]
    }
    ```
*   **Respuestas**:
    *   `201 Created`: Rol creado con su matriz de permisos asociada.
    *   `400 Bad Request`: Código duplicado o datos inválidos.

---

## 4. Módulo de Gestión de Usuarios

### GET `/administracion/usuarios/sugerir-username/?nombres=Juan&apellido=Perez`
*   **Propósito**: Endpoint utilitario para autocompletar el nombre de usuario sugerido y verificar colisiones.
*   **Permiso Requerido**: `modulo: 'usuarios'`, `accion: 'crear'`.
*   **Respuesta**:
    ```json
    {
      "sugerencia": "jperez",
      "disponible": true
    }
    ```
    *(Si `jperez` ya existe, devuelve `jperez1` o `jperez2` con `disponible: true`).*

### POST `/administracion/usuarios/crear/`
*   **Propósito**: Dar de alta a un usuario del sistema (cajero, lector, administrador).
*   **Permiso Requerido**: `modulo: 'usuarios'`, `accion: 'crear'`.
*   **Payload**:
    ```json
    {
      "username": "jperez",
      "nombres": "Juan",
      "apellido_paterno": "Pérez",
      "apellido_materno": "Gómez",
      "ci_numero": "6789123",
      "ci_expedido": "LP",
      "email": "jperez@comiteagua.bo",
      "telefono": "78945612",
      "rol_id": 2
    }
    ```
*   **Respuestas**:
    *   `201 Created`: Usuario creado con contraseña temporal generada aleatoriamente y `requiere_cambio_clave = true`. Devuelve ficha de enrolamiento lista para impresión:
        ```json
        {
          "status": "success",
          "usuario_id": 14,
          "username": "jperez",
          "clave_temporal_generada": "wK9#mQ2$xP",
          "ficha_impresion_url": "/administracion/usuarios/14/ficha-enrolamiento/"
        }
        ```

---

## 5. Módulo de Menús y Navegación Dinámica

### GET `/api/menus/arbol/`
*   **Propósito**: Devuelve la estructura jerárquica de menús visible para el usuario autenticado según sus permisos.
*   **Acceso**: Cualquier usuario autenticado.
*   **Respuesta**:
    ```json
    [
      {
        "id": 1,
        "titulo": "Inicio",
        "ruta": "/dashboard/",
        "icono": "home",
        "submenus": []
      },
      {
        "id": 2,
        "titulo": "Caja y Cobros",
        "ruta": "/caja/",
        "icono": "currency-dollar",
        "submenus": [
          {"titulo": "Cobro de Servicios", "ruta": "/caja/cobros/"},
          {"titulo": "Cierre de Turno", "ruta": "/caja/cierre/"}
        ]
      }
    ]
    ```

---

## 6. Módulo de Bitácora de Auditoría

### GET `/auditoria/`
*   **Propósito**: Consultar registros cronológicos de auditoría con filtros.
*   **Permiso Requerido**: `modulo: 'institucion'`, `accion: 'ver'` (o rol Auditor).
*   **Parámetros de Consulta**: `?fecha_desde=2026-10-01&fecha_hasta=2026-10-28&usuario_id=14&modulo=usuarios&accion=CREATE`.
*   **Respuesta**: `200 OK` con listado paginado inalterable de eventos.

