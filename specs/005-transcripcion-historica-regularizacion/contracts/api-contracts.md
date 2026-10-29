# Contratos de Interfaz y Endpoints: Fase 5 - Transcripción Histórica y Regularización (005-transcripcion-historica-regularizacion)

## 1. Mapeo de Rutas y Permisos

| Método | Ruta | Permiso Requerido | Descripción |
|---|---|---|---|
| `GET` | `/transcripcion/lotes/` | `TRANSCRIPCION:VER` | Listado y métricas de lotes de transcripción |
| `GET`, `POST` | `/transcripcion/lotes/crear/` | `TRANSCRIPCION:CREAR` | Creación de nuevo lote o planilla física |
| `GET` | `/transcripcion/lotes/<int:pk>/` | `TRANSCRIPCION:VER` | Detalle del lote, métricas de avance y registros |
| `GET`, `POST` | `/transcripcion/lotes/<int:lote_id>/capturar/` | `TRANSCRIPCION:CREAR` | Formulario de digitación de lecturas históricas |
| `POST` | `/transcripcion/registros/<int:pk>/validar/` | `TRANSCRIPCION:VALIDAR` | Aprobación formal por supervisor |
| `POST` | `/transcripcion/registros/<int:pk>/observar/` | `TRANSCRIPCION:VALIDAR` | Marcar observación con justificación |
| `POST` | `/transcripcion/registros/<int:pk>/rechazar/` | `TRANSCRIPCION:VALIDAR` | Rechazo justificado del registro histórico |
| `POST` | `/transcripcion/registros/<int:pk>/regularizar/` | `TRANSCRIPCION:VALIDAR` | Regularización a `Obligacion` económica (R-DOM-19) |
| `GET` | `/transcripcion/reporte/` | `TRANSCRIPCION:VER` | Reporte imprimible y exportable en formato CSV |

---

## 2. Contratos Detallados

### 2.1. `POST /transcripcion/lotes/<int:lote_id>/capturar/`
Permite transcribir una fila de lectura histórica proveniente del documento físico.

#### Parámetros (POST):
- `socio_id` (int, obligatorio): ID del socio.
- `medidor_id` (int, opcional): ID del medidor si figura en el cuaderno.
- `periodo` (string, obligatorio): Periodo histórico `YYYY-MM`.
- `lectura_anterior` (decimal, opcional): Lectura inicial registrada.
- `lectura_actual` (decimal, opcional): Lectura final registrada.
- `importe_documentado` (decimal, opcional): Monto manuscrito de la deuda si existía.
- `referencia_foja` (string, opcional): Referencia física (ej. "Libro 2, Foja 18").
- `observaciones` (string, opcional).

#### Validación:
- Si se ingresan ambas lecturas y `lectura_actual < lectura_anterior`, el registro se guarda con estado `OBSERVADA` y nota de discrepancia.
- Se previene duplicación del mismo medidor y periodo en el lote.

---

### 2.2. `POST /transcripcion/registros/<int:pk>/regularizar/`
Convierte un registro histórico validado en una `Obligacion` económica exigible en ventanilla de cobranza.

#### Parámetros (POST):
- `justificacion_respaldo` (string, obligatorio, mín. 10 caracteres): Acta, asamblea o documento que respalda la deuda.

#### Validación y Procesamiento Atómico (R-DOM-19):
1. El registro debe estar en estado `VALIDADO`.
2. Debe poseer un importe válido (`importe_documentado` o `importe_calculado` > 0).
3. No debe existir una `Obligacion` para ese socio, servicio y periodo.
4. Se crea la `Obligacion` en estado `PENDIENTE`.
5. El registro de transcripción pasa a `MIGRADO` vinculando `obligacion_regularizada`.
6. Se audita la regularización en `BitacoraAuditoria`.

