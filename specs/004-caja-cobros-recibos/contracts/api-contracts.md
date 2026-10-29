# Contratos de Interfaz y Endpoints: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## 1. Mapeo de Rutas y Permisos

| Método | Ruta | Permiso Requerido | Descripción |
|---|---|---|---|
| `GET` | `/caja/cobros/` | `CAJA:VER` | Pantalla de ventanilla de cobro y buscador de socio |
| `POST` | `/caja/cobros/procesar/` | `CAJA:CREAR` | Procesamiento transaccional de cobro multiconcepto |
| `GET` | `/caja/recibos/` | `CAJA:VER` | Listado histórico de recibos emitidos y anulados |
| `GET` | `/caja/recibos/<int:pk>/` | `CAJA:VER` | Vista e impresión oficial del recibo con QR |
| `POST` | `/caja/recibos/<int:pk>/anular/` | `CAJA:ANULAR` | Anulación autorizada con justificación y reversión |
| `GET`, `POST` | `/caja/turnos/apertura/` | `CAJA:CREAR` | Apertura de turno de caja con fondo inicial |
| `GET`, `POST` | `/caja/turnos/cierre/` | `CAJA:CERRAR` | Arqueo físico y cierre de turno activo |
| `GET` | `/caja/turnos/` | `CAJA:VER` | Historial y reporte de turnos cerrados |

---

## 2. Especificación Detallada de Contratos

### 2.1. `POST /caja/cobros/procesar/`
Procesa el pago de una o más obligaciones seleccionadas para un socio.

#### Parámetros Formulario (POST):
- `socio_id` (int, obligatorio): ID del socio titular.
- `obligaciones_ids` (list[int], obligatorio): IDs de las obligaciones seleccionadas para cancelar.
- `metodo_pago` (string, obligatorio): Uno de `EFECTIVO`, `QR`, `TRANSFERENCIA`.
- `referencia_transaccion` (string, opcional): Número de comprobante o referencia digital.

#### Validación y Reglas de Negocio:
1. El usuario debe tener un turno en estado `ABIERTA`.
2. Las obligaciones deben existir, pertenecer al socio indicado y estar en estado `PENDIENTE`.
3. Se bloquean las filas mediante `select_for_update()`.
4. El monto a cobrar es exactamente el 100% de la suma de las obligaciones (prohibición de pagos parciales R-DOM-15).
5. Se actualiza cada obligación a `PAGADA`, `saldo_pendiente = 0.00`.
6. Se crea el `Pago`, el `Recibo` correlativo y los `DetalleRecibo`.
7. Se registra auditoría P6.

#### Respuesta:
- **Éxito (302 Redirect)**: Redirige a `/caja/recibos/<pk>/` con mensaje de éxito `messages.success`.
- **Error (400 Bad Request o redirect con error)**: Si no hay turno abierto, si una obligación ya fue pagada, o si no se seleccionó ninguna obligación.

---

### 2.2. `POST /caja/recibos/<int:pk>/anular/`
Revierte los efectos de un recibo emitido erróneamente.

#### Parámetros Formulario (POST):
- `motivo` (string, obligatorio, mín. 10 caracteres): Justificación documentada de la anulación.

#### Validación y Reglas de Negocio:
1. Usuario con permiso `CAJA:ANULAR`.
2. El recibo debe estar en estado `EMITIDO`.
3. Transacción atómica:
   - Recibo pasa a `ANULADO`, guardando usuario y fecha.
   - Obligaciones asociadas en `DetalleRecibo` vuelven a `PENDIENTE` con `saldo_pendiente = monto`.
   - Se audita la anulación en `BitacoraAuditoria`.

#### Respuesta:
- **Éxito (302 Redirect)**: Redirige al detalle del recibo con mensaje de éxito.
- **Error (403 Forbidden / 400 Bad Request)**: Sin permiso o motivo inválido.

---

### 2.3. `POST /caja/turnos/apertura/`
Abre una nueva sesión de caja.

#### Parámetros Formulario (POST):
- `monto_apertura` (decimal, obligatorio, >= 0.00): Fondo inicial de caja para cambio.

#### Validación:
- El cajero autenticado no debe tener ya un turno en estado `ABIERTA`.

---

### 2.4. `POST /caja/turnos/cierre/`
Realiza el arqueo y cierre del turno del cajero autenticado.

#### Parámetros Formulario (POST):
- `monto_declarado_efectivo` (decimal, obligatorio, >= 0.00): Monto físico contado en gaveta.
- `observaciones_cierre` (string, opcional si diferencia == 0, obligatoria si hay diferencia).

#### Validación y Procesamiento:
- Calcula totales del sistema en efectivo y medios digitales.
- Calcula `diferencia_efectivo = monto_declarado_efectivo - (monto_apertura + total_efectivo_sistema)`.
- Marca el turno como `CERRADA`, guarda fecha de cierre y usuario.

