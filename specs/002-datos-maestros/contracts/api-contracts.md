# Contratos de Interfaz y Vistas: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 1 — Contratos de Interfaz, Endpoints y Permisos RBAC  
> **Fecha:** Octubre 2026  

---

## 1. Matriz de Endpoints y Permisos RBAC

Todas las vistas validan obligatoriamente los permisos mediante el decorador server-side `@requiere_permiso(modulo, accion)`. Cualquier intento no autorizado responde con código HTTP `403 Forbidden` y se audita como `ACCESS_DENIED`.

| Módulo | Ruta URL | Método | Permiso RBAC Requerido | Descripción / Efecto |
|---|---|---|---|---|
| **Zonas** | `/zonas/` | `GET` | `ZONAS:VER` | Listado paginado de zonas y filtros de búsqueda |
| **Zonas** | `/zonas/crear/` | `GET`, `POST` | `ZONAS:CREAR` | Formulario de alta de zona territorial |
| **Zonas** | `/zonas/<int:pk>/editar/` | `GET`, `POST` | `ZONAS:EDITAR` | Edición de datos de una zona |
| **Zonas** | `/zonas/<int:pk>/desactivar/` | `POST` | `ZONAS:DESACTIVAR` | Desactivación lógica de zona (impide `DELETE`) |
| **Servicios** | `/servicios/` | `GET` | `SERVICIOS:VER` | Catálogo de servicios y modalidades de cobro |
| **Servicios** | `/servicios/crear/` | `GET`, `POST` | `SERVICIOS:CREAR` | Formulario de alta de un servicio |
| **Servicios** | `/servicios/<int:pk>/editar/` | `GET`, `POST` | `SERVICIOS:EDITAR` | Edición de catálogo de servicios |
| **Tarifarios** | `/servicios/tarifarios/` | `GET` | `TARIFAS:VER` | Listado de tarifarios y vigencias |
| **Tarifarios** | `/servicios/tarifarios/crear/` | `GET`, `POST` | `TARIFAS:ADMIN` | Definición de tarifario, tramos y vigencias |
| **Tarifarios** | `/servicios/tarifarios/<int:pk>/` | `GET` | `TARIFAS:VER` | Detalle de tramos y reglas de cálculo de una tarifa |
| **Medidores** | `/medidores/` | `GET` | `MEDIDORES:VER` | Inventario de medidores y filtros por estado |
| **Medidores** | `/medidores/crear/` | `GET`, `POST` | `MEDIDORES:CREAR` | Alta de medidor físico con serie y lectura inicial |
| **Medidores** | `/medidores/<int:pk>/editar/` | `GET`, `POST` | `MEDIDORES:EDITAR` | Edición de características técnicas |
| **Medidores** | `/medidores/<int:pk>/asignar/` | `GET`, `POST` | `MEDIDORES:ASIGNAR` | Asignación exclusiva de medidor a socio |
| **Medidores** | `/medidores/asignaciones/<int:pk>/retirar/` | `GET`, `POST` | `MEDIDORES:ASIGNAR` | Desasignación con lectura final de retiro |
| **Socios** | `/socios/` | `GET` | `SOCIOS:VER` | Padrón de socios con búsqueda por CI, nombre, zona |
| **Socios** | `/socios/crear/` | `GET`, `POST` | `SOCIOS:CREAR` | Alta de socio con generación atómica de membresía |
| **Socios** | `/socios/<int:pk>/` | `GET` | `SOCIOS:VER` | Ficha integral 360° del socio |
| **Socios** | `/socios/<int:pk>/editar/` | `GET`, `POST` | `SOCIOS:EDITAR` | Edición de datos personales y predio |
| **Socios** | `/socios/<int:pk>/estado/` | `POST` | `SOCIOS:EDITAR` | Transición de estado (`ACTIVO`, `INACTIVO`, etc.) |

---

## 2. Contratos de Formularios y Validaciones

### 2.1. Formulario de Alta de Socio (`SocioForm`)
- **Entrada:**
  ```json
  {
    "ci": "4892019",
    "ci_complemento": "",
    "nombres": "Juan Carlos",
    "apellidos": "Mamani Choque",
    "zona": 1,
    "direccion": "Av. Panamericana N° 45, Lote 12",
    "telefono": "71234567",
    "email": "juan.mamani@email.com",
    "fecha_ingreso": "2026-10-28",
    "observaciones": "Afiliación ordinaria"
  }
  ```
- **Validaciones de Negocio:**
  - `ci` obligatorio. Se valida unicidad compuesta `(ci, ci_complemento)`. Si colisiona: *"Ya existe un socio registrado con el CI 4892019"*.
  - `zona` obligatoria y debe ser una zona activa.
  - Al guardar: se invoca el servicio `registrar_socio()` en bloque atómico que:
    1. Genera código correlativo (ej. `SOC-0001`).
    2. Crea al socio.
    3. Emite la obligación de membresía única no recurrente (R-DOM-13).
    4. Audita la operación en `BitacoraAuditoria`.

### 2.2. Formulario de Asignación de Medidor (`AsignarMedidorForm`)
- **Entrada:**
  ```json
  {
    "socio_id": 1,
    "medidor_id": 5,
    "fecha_asignacion": "2026-10-28",
    "lectura_instalacion": "0.00",
    "observaciones": "Instalación en nicho frontal con candado"
  }
  ```
- **Validaciones de Negocio:**
  - El medidor debe encontrarse en estado `DISPONIBLE`. Si ya está asignado o en mantenimiento: *"El medidor MED-0005 no está disponible para asignación (Estado actual: INSTALADO)"*.
  - `lectura_instalacion` no puede ser negativa.
  - Al confirmar:
    1. Se crea `AsignacionMedidor` (`activo = True`).
    2. El medidor pasa a estado `INSTALADO`.
    3. Se audita la asignación con el socio y medidor vinculados.

### 2.3. Formulario de Retiro de Medidor (`RetirarMedidorForm`)
- **Entrada:**
  ```json
  {
    "fecha_retiro": "2026-10-28",
    "lectura_retiro": "154.20",
    "motivo_retiro": "Sustitución por medidor de mayor caudal",
    "nuevo_estado_medidor": "MANTENIMIENTO"
  }
  ```
- **Validaciones de Negocio:**
  - `lectura_retiro` obligatoria.
  - Validación de consistencia: `lectura_retiro >= lectura_instalacion`. Si es menor: *"La lectura de retiro (154.20) no puede ser menor a la lectura de instalación (200.00)"*.
  - Al confirmar:
    1. La asignación pasa a `activo = False`, registrando `fecha_retiro`, `lectura_retiro` y `motivo_retiro`.
    2. El medidor pasa al estado indicado (`MANTENIMIENTO`, `DISPONIBLE`, etc.).
    3. Se audita la operación conservando todo el historial.

