# Decisiones de Diseño y Arquitectura: Fase 6 - Reportes Administrativos y Financieros (006-reportes-administrativos-financieros)

## 1. Justificación y Contexto
La Sección 10 de la fuente funcional y la Constitución SDD v1.0 imponen que todos los reportes deben derivarse de datos consistentes y auditables (Principio P2), distinguiendo claramente lo facturado, lo cobrado, lo pendiente y lo anulado (Principio P8).

---

## 2. Registro de Decisiones de Arquitectura (ADR)

### DEC-034: Arquitectura de la Aplicación `apps/reportes` (Sin Duplicación de Modelos)
- **Contexto**: Los reportes son vistas analíticas agregadas sobre datos transaccionales existentes (`apps.socios`, `apps.servicios`, `apps.medidores`, `apps.consumo`, `apps.caja`, `apps.transcripcion`).
- **Decisión**: La aplicación `apps.reportes` no creará tablas duplicadas ni desnormalizaciones redundantes. Consistirá en:
  - Una capa de servicios analíticos (`apps.reportes.services`) con consultas agregadas optimizadas.
  - Vistas y exportadores a CSV/impresión física.
- **Consecuencias**: Garantiza el Principio P2 (Fuente Única de Verdad), eliminando desincronizaciones contables.

---

### DEC-035: Cálculo Agregado de Deudores sin Duplicaciones (Sección 10.1)
- **Contexto**: Un socio puede tener varias deudas de agua, una de membresía y otras por reconexión. La suma no debe duplicar socios ni montos.
- **Decisión**:
  - Se consulta `Socio.objects.filter(activo=True, obligaciones__estado=EstadoObligacion.PENDIENTE).distinct()`.
  - Para cada socio, se desglosa mediante agregaciones condicionales o métodos eficientes:
    - `deuda_agua`: suma de saldos pendientes con `servicio__tipo_servicio == AGUA_POTABLE`.
    - `deuda_membresia`: suma de saldos pendientes con `servicio__tipo_servicio == MEMBRESIA`.
    - `deuda_otros`: suma de saldos pendientes con otros servicios.
    - `total_pendiente = deuda_agua + deuda_membresia + deuda_otros`.
    - `importe_vencido`: suma de saldos pendientes con `fecha_vencimiento < hoy`.
    - `meses_antiguedad`: cantidad de periodos mensuales adeudados.
- **Consecuencias**: Máxima precisión contable y cumplimiento estricto de la Sección 10.1.

---

### DEC-036: Conciliación de Recaudación Neta vs Anulaciones (Sección 10.5)
- **Contexto**: La sección 10.5 exige que el reporte de recaudación refleje pagos efectivamente recibidos y distinga los recibos anulados.
- **Decisión**:
  - Se analizan las instancias de `Recibo`:
    - `recibos_emitidos`: aquellos con `estado == 'EMITIDO'`. Su suma conforma la **Recaudación Neta**.
    - `recibos_anulados`: aquellos con `estado == 'ANULADO'`. Se cuantifican y muestran por separado sin restarlos de la recaudación neta real (puesto que al anularse nunca se integraron a fondos o fueron revertidos).
  - Los ingresos netos se desglosan por `metodo_pago` (`EFECTIVO`, `QR`, `TRANSFERENCIA`).
- **Consecuencias**: Transparencia contable total (P8).

---

### DEC-037: Membrete Institucional y Formato Apto para Impresión Física
- **Contexto**: Los reportes se presentan en asambleas comunitarias y deben cumplir formalidades visuales.
- **Decisión**:
  - Todas las plantillas de reportes integran el membrete institucional obtenido desde `Institucion.get_solo()` (nombre, NIT/personería, dirección, teléfono, logo).
  - Estilos CSS específicos `@media print` para ocultar barras de navegación, botones y paginadores al imprimir o generar PDF mediante el navegador.
- **Consecuencias**: Aspecto profesional y uniformidad institucional.

---

### DEC-038: Control de Descargas CSV y Auditoría de Exportación (P6, P7)
- **Contexto**: La exportación masiva de datos personales o financieros requiere control de seguridad.
- **Decisión**:
  - El parámetro `?format=csv` está protegido por el permiso server-side `REPORTES:EXPORTAR`.
  - Cada exportación genera un evento en `BitacoraAuditoria` con el usuario, módulo, acción `EXPORTAR_REPORTE` y filtros aplicados.
- **Consecuencias**: Cumplimiento de los principios P6 (Auditoría) y P7 (Seguridad).

