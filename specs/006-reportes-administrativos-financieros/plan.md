# Plan de Implementación: Fase 6 - Reportes Administrativos (006-reportes-administrativos-financieros)

## 1. Verificación Constitucional Previa (Constitution Check)

| Principio / Regla | Estado | Mecanismo de Garantía |
|---|---|---|
| **P1. Fidelidad de Negocio** | Cumple | Reportes ajustados textualmente a los requerimientos de la Sección 10 de la fuente. |
| **P2. Fuente Única de Verdad** | Cumple | Todos los totales provienen de agregaciones dinámicas del ORM sobre tablas operativas. |
| **P5. Conservación Histórica** | Cumple | Se incluyen análisis de estados históricos y recibos anulados. |
| **P6. Auditoría Verificable** | Cumple | Registro inmutable de cada exportación CSV en `BitacoraAuditoria`. |
| **P7. Seguridad por Defecto** | Cumple | Permisos `REPORTES:VER` y `REPORTES:EXPORTAR` validados en servidor. |
| **P8. Transparencia Financiera** | Cumple | Distinción contable estricta entre recaudación neta, obligaciones emitidas y anuladas. |

---

## 2. Fases de Ejecución

### Fase 6.1: Estructura Base y Servicios Analíticos
1. Crear la app `apps/reportes` y registrarla en `config/settings.py`.
2. Implementar los servicios en `apps/reportes/services.py`:
   - `obtener_reporte_deudores(...)`
   - `obtener_reporte_recaudacion(...)`
   - `obtener_reporte_consumo(...)`
   - `obtener_reporte_zonas(...)`
   - `obtener_reporte_membresias(...)`
   - `obtener_estado_cuenta_socio(...)`

### Fase 6.2: Pruebas Automatizadas (TDD)
1. Tests para agregaciones de deudores, desglose por concepto y antigüedad en `tests/test_reportes_deudores.py`.
2. Tests para cuadre de recaudación neta, medios de pago y recibos anulados en `tests/test_reportes_recaudacion.py`.
3. Tests para consumo volumétrico y vistas web con exportación CSV en `tests/test_reportes_views.py`.

### Fase 6.3: Interfaz de Usuario y Vistas
1. Vistas en `apps/reportes/views.py`.
2. Plantillas HTML en `templates/reportes/`:
   - `dashboard.html`: Panel ejecutivo central con enlaces y resúmenes.
   - `deudores.html`: Reporte de deudores con filtros y vista imprimible.
   - `recaudacion.html`: Reporte de recaudación por medio de pago.
   - `consumo.html`: Reporte de consumo y anomalías observadas.
   - `zonas.html`: Balance integral por zona.
   - `membresias.html`: Estado de afiliaciones únicas.
   - `socio_estado_cuenta.html`: Estado de cuenta individual 360°.

### Fase 6.4: Navegación, Rutas y Certificación
1. Vincular rutas en `config/urls.py` y actualizar `fixtures/seed_menus.json`.
2. Ejecutar `pytest` y verificar 100% PASS en toda la suite.
3. Actualizar `CLAUDE.md`.

