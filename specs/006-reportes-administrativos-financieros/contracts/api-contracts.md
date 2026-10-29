# Contratos de Interfaz y Endpoints: Fase 6 - Reportes Administrativos (006-reportes-administrativos-financieros)

## 1. Mapeo de Rutas y Permisos

| Método | Ruta | Permiso Requerido | Descripción |
|---|---|---|---|
| `GET` | `/reportes/` | `REPORTES:VER` | Dashboard central de reportes ejecutivos |
| `GET` | `/reportes/deudores/` | `REPORTES:VER` | Reporte consolidado de deudores y morosidad |
| `GET` | `/reportes/recaudacion/` | `REPORTES:VER` | Reporte de ingresos cobrados por forma de pago |
| `GET` | `/reportes/consumo/` | `REPORTES:VER` | Reporte de volumen consumido y anomalías |
| `GET` | `/reportes/zonas/` | `REPORTES:VER` | Reporte de balance territorial por sector |
| `GET` | `/reportes/membresias/` | `REPORTES:VER` | Reporte de incorporaciones y afiliaciones |
| `GET` | `/reportes/socio/<int:socio_id>/` | `REPORTES:VER` | Estado de cuenta 360° individual del socio |

*Nota:* Cualquier solicitud con el parámetro `format=csv` exige además el permiso `REPORTES:EXPORTAR`.

---

## 2. Parámetros de Consulta por Endpoint

### 2.1. `GET /reportes/deudores/`
- `zona` (int, opcional): Filtrar por ID de zona.
- `antiguedad` (int, opcional): Filtrar socios con mora >= N periodos.
- `solo_vencidas` (bool/string, opcional): Si '1', incluye únicamente obligaciones cuya `fecha_vencimiento < hoy`.
- `format` (string, opcional): 'csv' para descarga de archivo.

### 2.2. `GET /reportes/recaudacion/`
- `fecha_desde` (string, YYYY-MM-DD, opcional): Inicio del rango.
- `fecha_hasta` (string, YYYY-MM-DD, opcional): Fin del rango.
- `cajero` (int, opcional): Filtrar por ID de usuario cajero.
- `metodo` (string, opcional): Uno de `EFECTIVO`, `QR`, `TRANSFERENCIA`.
- `format` (string, opcional): 'csv'.

### 2.3. `GET /reportes/consumo/`
- `periodo` (string, YYYY-MM, opcional): Periodo de consumo. Por defecto, mes en curso o último facturado.
- `zona` (int, opcional): Filtrar por ID de zona.
- `format` (string, opcional): 'csv'.

### 2.4. `GET /reportes/membresias/`
- `zona` (int, opcional): Filtrar por zona.
- `estado` (string, opcional): `PENDIENTE` o `PAGADA`.
- `format` (string, opcional): 'csv'.

