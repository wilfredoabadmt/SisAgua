# Contratos de Interfaz y Vistas: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 1 — Contratos de Interfaz, Endpoints y Permisos RBAC  
> **Fecha:** Octubre 2026  

---

## 1. Matriz de Endpoints y Permisos RBAC

| Módulo | Ruta URL | Método | Permiso RBAC Requerido | Descripción / Efecto |
|---|---|---|---|---|
| **Consumo** | `/consumo/lecturas/` | `GET` | `LECTURAS:VER` | Listado de lecturas por periodo (`YYYY-MM`) y zona |
| **Consumo** | `/consumo/lecturas/capturar/` | `GET`, `POST` | `LECTURAS:CREAR` | Formulario de captura de lectura mensual con cálculo inmediato |
| **Consumo** | `/consumo/lecturas/<int:pk>/corregir/` | `GET`, `POST` | `LECTURAS:MODIFICAR` | Corrección o justificación de lectura observada |
| **Consumo** | `/consumo/observadas/` | `GET` | `LECTURAS:VER` | Bandeja de control y supervisión de lecturas observadas |
| **Consumo** | `/consumo/proformas/<int:pk>/` | `GET` | `LECTURAS:VER` | Proforma informativa de medición para el socio (R-DOM-09) |
| **Consumo** | `/consumo/facturacion/` | `GET` | `CONSUMO:GENERAR` | Panel de control de facturación mensual y resumen del periodo |
| **Consumo** | `/consumo/facturacion/ejecutar/` | `POST` | `CONSUMO:GENERAR` | Ejecución del motor idempotente de cálculo y emisión de obligaciones |

---

## 2. Contratos de Formularios y Validaciones

### 2.1. Formulario de Captura de Lectura (`CapturaLecturaForm`)
- **Entrada:**
  ```json
  {
    "periodo": "2026-10",
    "medidor_id": 1,
    "lectura_actual": "137.00",
    "fecha_lectura": "2026-10-28",
    "observaciones": "Lectura tomada con visor limpio"
  }
  ```
- **Lógica de Validación:**
  - El sistema resuelve la `lectura_anterior` válida (ej. `125.00` $m^3$).
  - Calcula consumo: $\text{Consumo} = 137.00 - 125.00 = 12.00 \text{ m}^3$.
  - Si `lectura_actual < lectura_anterior` (ej. `120.00`):
    - Se registra con `estado = 'OBSERVADA'` y advertencia en pantalla: *"Lectura menor a la anterior. Registro marcado como OBSERVADO (R-DOM-07) para revisión previa."*
  - Si `lectura_actual >= lectura_anterior`:
    - Se registra con `estado = 'VALIDADA'`.
  - Idempotencia: Si ya existe lectura activa para ese medidor y periodo, rechaza duplicación (R-DOM-08).

### 2.2. Formulario de Corrección de Lectura (`CorregirLecturaForm`)
- **Entrada:**
  ```json
  {
    "nueva_lectura": "138.50",
    "motivo_correccion": "Error de tipeo del lector de campo verificado en contra-lectura",
    "es_reinicio_contador": false
  }
  ```
- **Efecto:**
  - Actualiza la lectura a `estado = 'CORREGIDA'`.
  - Recalcula el consumo.
  - Registra al supervisor en `validado_por` y fecha en `fecha_validacion`.
  - Registra auditoría con valor previo y nuevo (P5, P6).

### 2.3. Ejecución del Motor de Facturación (`EjecutarFacturacionForm`)
- **Entrada:**
  ```json
  {
    "periodo": "2026-10"
  }
  ```
- **Respuesta (JSON o Redirección con Mensaje):**
  ```json
  {
    "periodo": "2026-10",
    "obligaciones_generadas": 45,
    "obligaciones_omitidas_idempotencia": 0,
    "lecturas_observadas_omitidas": 2,
    "monto_total_devengado_bs": "780.00"
  }
  ```

