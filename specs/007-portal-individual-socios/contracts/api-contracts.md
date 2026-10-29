# Contratos de Interfaz y Endpoints: Fase 7 - Portal de Socios (007-portal-individual-socios)

## 1. Mapeo de Rutas y Permisos

| Método | Ruta | Permiso Requerido | Descripción |
|---|---|---|---|
| `GET` | `/portal/` | `PORTAL:VER` | Panel principal del socio autenticado (resumen 360°, deuda actual y último consumo) |
| `GET` | `/portal/medidores/` | `PORTAL:VER` | Consulta detallada de medidores asignados y lecturas mensuales |
| `GET` | `/portal/deudas/` | `PORTAL:VER` | Detalle de obligaciones pendientes de pago y mora vencida |
| `GET` | `/portal/recibos/` | `PORTAL:VER` | Historial de recibos oficiales emitidos |
| `GET` | `/portal/recibo/<int:recibo_id>/` | `PORTAL:VER` | Visualización e impresión de recibo oficial propio (aislado IDOR) |
| `GET` | `/portal/proforma/<str:periodo>/` | `PORTAL:VER` | Visualización e impresión de proforma informativa mensual (R-DOM-09) |
| `GET/POST` | `/portal/perfil/` | `PORTAL:VER` | Actualización de datos de contacto (teléfono y correo) y cambio de contraseña |
| `POST` | `/socios/<int:socio_id>/habilitar-portal/` | `SOCIOS:MODIFICAR` | Generación de cuenta de acceso y entrega de credenciales temporales por administración |

## 2. Parámetros y Validaciones
- **Seguridad IDOR:** Si un socio intenta consultar un recibo con un ID que no le pertenece, se responde con HTTP 404 (ocultando existencia) o 403.
- **Auditoría:** La actualización de teléfono/correo y el acceso al portal se registran con `modulo='PORTAL'`.

