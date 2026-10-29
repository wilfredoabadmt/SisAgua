# SisAgua — Guía para Claude y Agentes SDD

> **Proyecto:** Sistema de Administración, Consumo y Cobro de Agua Potable (SisAgua)  
> **Metodología:** Spec-Driven Development (SDD) con Spec Kit  
> **Constitución Oficial:** [.specify/memory/constitution.md](.specify/memory/constitution.md)  
> **Documento Rector Consolidado:** [CONSTITUCION_SDD_v1.0.md](CONSTITUCION_SDD_v1.0.md)  
> **Fuente Funcional:** `SISTEMA DE ADMINISTRACION.docx` (40 págs., 882 párrafos)  
> **Estado Actual:** LAS 8 FASES CANÓNICAS ESTÁN 100% COMPLETADAS Y CERTIFICADAS (112/112 Tests PASS)  
> **Sistema Certificado:** SisAgua v1.0 listo para producción institucional bajo Ley N° 2066 y directrices AAPS  

---

## Certificación del Sistema Completo (8 Fases Canónicas)

Todas las fases estipuladas en la Sección 15 y el documento funcional primario de 40 páginas (`SISTEMA DE ADMINISTRACION.docx`) han sido implementadas y certificadas bajo la metodología **Spec-Driven Development (SDD)** con aprobación total de las pruebas automatizadas (112/112 tests PASS):

1. [x] **Fase 1 (001-configuracion-seguridad):** Configuración institucional, seguridad Argon2id, roles y permisos server-side, auditoría sanitizada.
2. [x] **Fase 2 (002-datos-maestros):** Zonas territoriales, padrón de socios (CI + complemento), membresía única atómica (R-DOM-13), catálogo de servicios, tarifarios escalonados sin retroactividad (R-DOM-10), parque de medidores y asignación exclusiva (R-DOM-03).
3. [x] **Fase 3 (003-consumo-lecturas-calculo):** Monitoreo mensual de consumos ($m^3$), validación de monotonicidad (R-DOM-07), proforma informativa (R-DOM-09) y motor de facturación determinístico e idempotente (R-DOM-11/12/14).
4. [x] **Fase 4 (004-caja-cobros-recibos):** Ventanilla de cobro, prohibición de pagos parciales (R-DOM-15), cobro multiconcepto transaccional ACID (R-DOM-16), recibo oficial correlativo inalterable (`REC-YYYY-000001`) con QR y literal boliviano, anulación autorizada con reversión íntegra (R-DOM-17, P5), control de turnos y arqueos físicos con registro de diferencias.
5. [x] **Fase 5 (005-transcripcion-historica-regularizacion):** Gestión documental de lotes, máquina de estados normativa (`PENDIENTE` a `MIGRADO`), distinción entre lectura histórica y deuda exigible (R-DOM-18), y regularización trazable de deudas históricas respaldadas (R-DOM-19).
6. [x] **Fase 6 (006-reportes-administrativos-financieros):** Reporte de deudores consolidado por concepto y antigüedad en mora (Sección 10.1), reporte de recaudación neta efectiva por forma de pago con discriminación de recibos anulados (Sección 10.5), análisis volumétrico de consumo y anomalías (Sección 10.4), balance territorial por zona (Sección 10.2), reporte de membresías (Sección 10.6), estado de cuenta individual 360° (Sección 10.3), membrete oficial e impresión `@media print`, y exportación CSV auditada y autorizada por RBAC.
7. [x] **Fase 7 (007-portal-individual-socios):** Portal individual de autoservicio para socios comunitarios (Sección 11), aislamiento estricto de identidad multitenant a nivel fila contra IDOR (Principio P7, R-DOM-01), consulta de medidores y lecturas, proforma informativa mensual (R-DOM-09), historial de recibos oficiales, actualización autónoma de datos de contacto y cambio de contraseña.
8. [x] **Fase 8 (008-auditoria-final-puesta-en-marcha):** Auditoría automatizada de integridad cruzada (`verificar_integridad_sistema`) conforme a las 9 reglas de la Sección 13, motor de respaldos institucionales serializados con manifiesto y checksum SHA-256 (`backup_institucional`), y pruebas de integración cruzada de fin de ciclo.

---

## Features completadas y certificadas:

### 1. 001-configuracion-seguridad (COMPLETADA Y VERIFICADA AL 100% - 20 Tests)
Plan técnico: [specs/001-configuracion-seguridad/plan.md](specs/001-configuracion-seguridad/plan.md).
- Parametrización institucional (Singleton con logo, moneda Bs, leyenda oficial).
- Custom User Model con Argon2id como default hasher, forzado de cambio de clave temporal y bloqueo de fuerza bruta tras 5 intentos.
- Matriz RBAC server-side con decorador `@requiere_permiso(modulo, accion)`.
- Menús dinámicos dependientes de permisos de rol y context processor institucional.
- Bitácora inalterable (Append-Only) `BitacoraAuditoria` con sanitización recursiva de secretos.

### 2. 002-datos-maestros (COMPLETADA Y VERIFICADA AL 100% - 27 Tests)
Plan técnico: [specs/002-datos-maestros/plan.md](specs/002-datos-maestros/plan.md) | Tasks: [specs/002-datos-maestros/tasks.md](specs/002-datos-maestros/tasks.md).
- **Zonas Territoriales (`apps.socios.models.Zona`):** Código único en mayúsculas, descripción, responsable, bloqueo estricto de borrado físico (`DELETE` interceptado) y desactivación lógica (Principio P5).
- **Catálogo de Servicios (`apps.servicios.models.Servicio`):** Modalidades catalogadas (`LECTURA_VOLUMETRICA`, `PAGO_UNICO_MEMBRESIA`, `CUOTA_FIJA_MENSUAL`, `EVENTUAL`).
- **Padrón de Socios (`apps.socios.models.Socio`):** Cédula de Identidad única con complemento boliviano (`unique_socio_ci_complemento`), autogeneración correlativa de código (`SOC-XXXX`), y **alta atómica con emisión indivisible de la membresía única (R-DOM-13)**.
- **Parque de Medidores (`apps.medidores.models.Medidor`):** Inventario con número de serie único, diámetro, lectura inicial y estado operativo.
- **Asignación Exclusiva de Medidores (`apps.medidores.models.AsignacionMedidor`):** Restricción en base de datos `UniqueConstraint(fields=['medidor'], condition=Q(activo=True))` que impide asignación concurrente (R-DOM-03); soporte de múltiples medidores por socio (R-DOM-02); retiro con registro obligatorio de lectura final (R-DOM-04).
- **Esquema Tarifario (`apps.servicios.models.Tarifario` y `TramoTarifario`):** Resolución determinística de tarifa vigente por fecha y categoría; bloqueo absoluto de retroactividad (R-DOM-10).
- **Ficha Integral 360° del Socio:** Vista consolidada de predio, medidores activos, historial de medidores sustituidos y obligaciones devengadas.

### 3. 003-consumo-lecturas-calculo (COMPLETADA Y VERIFICADA AL 100% - 14 Tests)
Plan técnico: [specs/003-consumo-lecturas-calculo/plan.md](specs/003-consumo-lecturas-calculo/plan.md) | Tasks: [specs/003-consumo-lecturas-calculo/tasks.md](specs/003-consumo-lecturas-calculo/tasks.md).
- **Captura de Lecturas Mensuales (`apps.consumo.models.Lectura`):** Determinación automática de la lectura anterior válida de partida (R-DOM-06), cálculo inmediato del consumo en metros cúbicos ($m^3$).
- **Validación de Monotonicidad (R-DOM-07):** Bloqueo automático ante lecturas inferiores a la anterior clasificando la lectura como `OBSERVADA` y excluyéndola de la facturación automática (Principio P10).
- **Unicidad de Lectura Definitiva (R-DOM-08):** Restricción `unique_lectura_activa_por_medidor_periodo` a nivel de base de datos.
- **Trazabilidad de Correcciones (P5, P6):** Rectificación autorizada por supervisor con justificación obligatoria y auditoría inmutable. Soporte para reinicio de contador (*rollover* tras 99999).
- **Proforma Informativa de Medición (R-DOM-09):** Comprobante para el socio con historial real de hasta 3 lecturas anteriores sin fabricación de datos y leyenda expresa de no-recibo.
- **Motor de Facturación Idempotente (R-DOM-11, R-DOM-12, R-DOM-14):** Generación atómica en lote de cuentas por cobrar devengadas congelando el snapshot tarifario y calculando vencimientos determinísticos de fin de mes.

### 4. 004-caja-cobros-recibos (COMPLETADA Y VERIFICADA AL 100% - 14 Tests)
Plan técnico: [specs/004-caja-cobros-recibos/plan.md](specs/004-caja-cobros-recibos/plan.md) | Tasks: [specs/004-caja-cobros-recibos/tasks.md](specs/004-caja-cobros-recibos/tasks.md).
- **Control de Turnos y Arqueo (`apps.caja.models.CajaTurno`):** Apertura formal con fondo de cambio, cobros asociados al cajero en turno, cálculo en tiempo real de cobros en efectivo y digitales, arqueo físico con registro de diferencias y justificación obligatoria (Sección 9.5).
- **Prohibición Absoluta de Pagos Parciales (R-DOM-15):** Liquidación obligatoria del 100% de cada obligación seleccionada; el cajero solo selecciona qué obligaciones saldar sin fraccionar saldos individuales.
- **Cobro Multiconcepto Transaccional (R-DOM-16):** Liquidación en bloque ACID con bloqueo pesimista `select_for_update()` para agua, membresías u otros servicios, actualización de `Obligacion` a `PAGADA`, emisión de `Pago` y acumulación en turno de caja.
- **Emisión Oficial de Recibo Inalterable (R-DOM-17):** Numeración correlativa anual institucional inalterable (`REC-YYYY-000001`), monto literal boliviano, código de verificación/QR, saldo remanente y prohibición de borrado físico (`DELETE` interceptado por P5).
- **Anulación Autorizada y Reversión Automática (R-DOM-17, P5, P6):** Procedimiento formal para supervisores con justificación documentada (>= 10 caracteres) que revierte atómicamente las obligaciones a `PENDIENTE` sin eliminar el recibo histórico.

### 5. 005-transcripcion-historica-regularizacion (COMPLETADA Y VERIFICADA AL 100% - 15 Tests)
Plan técnico: [specs/005-transcripcion-historica-regularizacion/plan.md](specs/005-transcripcion-historica-regularizacion/plan.md) | Tasks: [specs/005-transcripcion-historica-regularizacion/tasks.md](specs/005-transcripcion-historica-regularizacion/tasks.md).
- **Gestión Documental de Lotes (`apps.transcripcion.models.LoteTranscripcion`):** Organización de la captura por cuaderno, empadronamiento o planilla física, con registro de fuente y meta estimada para control de avance (Sección 8.1).
- **Máquina de Estados de Transcripción (Sección 8.3):** Ciclo normativo estricto: `PENDIENTE`, `TRANSCRITO`, `OBSERVADO`, `VALIDADO`, `MIGRADO`, `RECHAZADO`, con trazabilidad de transcriptor, validador y marcas temporales (P6).
- **Distinción entre Lectura Histórica y Deuda Exigible (R-DOM-18):** La captura y validación de una lectura antigua NO altera el saldo adeudado del socio ni genera obligaciones de cobro automáticas.
- **Regularización Trazable de Deuda Histórica (R-DOM-19):** Incorporación formal de deudas respaldadas al estado de cuenta del socio mediante transacción atómica que genera una `Obligacion` en `servicios`, vinculándola con la transcripción original para posterior cobranza en caja con recibo oficial.
- **Métricas de Avance y Reporte Exportable (Secciones 8.5 y 8.6):** Cuadro de mando con cálculo honesto del avance por etapa, vista imprimible membretada y exportación en formato CSV.

### 6. 006-reportes-administrativos-financieros (COMPLETADA Y VERIFICADA AL 100% - 10 Tests)
Plan técnico: [specs/006-reportes-administrativos-financieros/plan.md](specs/006-reportes-administrativos-financieros/plan.md) | Tasks: [specs/006-reportes-administrativos-financieros/tasks.md](specs/006-reportes-administrativos-financieros/tasks.md).
- **Reporte de Deudores Consolidado (Sección 10.1):** Agrupación estricta por socio sin duplicación de registros por múltiples medidores u obligaciones; desglose por concepto (Agua, Membresía, Otros), total pendiente, importe vencido y antigüedad en meses de mora.
- **Reporte de Recaudación Efectiva (Sección 10.5):** Conciliación neta de ingresos reales exclusivamente de recibos emitidos con desglose por medio de pago (`EFECTIVO`, `QR`, `TRANSFERENCIA`); informe y cuantificación separada de recibos anulados para auditoría contable.
- **Reporte de Consumo Volumétrico (Sección 10.4):** Monitoreo de metros cúbicos ($m^3$), consumo promedio por conexión, detección de consumos cero (0 $m^3$) y lecturas observadas.
- **Balance Territorial por Zona (Sección 10.2):** Comparativa sectorial de padrón de socios (activos/inactivos), parque de medidores, total facturado vs. recaudado y porcentaje de eficacia de cobro.
- **Reporte de Estado de Membresías (Sección 10.6):** Seguimiento a las cuotas de incorporación única originadas en el alta de socios.
- **Estado de Cuenta Individual 360° (Sección 10.3):** Ficha consolidada de predio, medidores asignados, cargos devengados y recibos oficiales cancelados.
- **Membrete Oficial y Exportación Segura (P6, P7):** Membrete institucional oficial (`Institucion.get_solo()`) en todas las vistas imprimibles `@media print`, y exportación a CSV con validación server-side del permiso `REPORTES:EXPORTAR` y registro inmutable en `BitacoraAuditoria`.

### 7. 007-portal-individual-socios (COMPLETADA Y VERIFICADA AL 100% - 6 Tests)
Plan técnico: [specs/007-portal-individual-socios/plan.md](specs/007-portal-individual-socios/plan.md) | Tasks: [specs/007-portal-individual-socios/tasks.md](specs/007-portal-individual-socios/tasks.md).
- **Aislamiento Estricto de Identidad Multitenant a Nivel Fila (Principio P7, R-DOM-01):** El socio autenticado accede exclusivamente a sus propios registros (`request.user.perfil_socio`). Intentos de manipulación IDOR (`/portal/recibo/<otro_id>/`) son rechazados con HTTP 404/403.
- **Habilitación de Cuenta Institucional (Sección 11 y 12.1):** Generación de username determinístico sin colisiones (`jperez`), contraseña temporal criptográfica de alta entropía con flag `requiere_cambio_clave=True`, rol `SOCIO` y permiso `PORTAL:VER`.
- **Panel Integral 360° del Socio:** Resumen inmediato de saldo adeudado, discriminación de mora vencida, última medición volumétrica y accesos directos responsivos (mobile-first).
- **Monitoreo de Parque de Medidores y Lecturas:** Listado de conexiones activas e históricas con histórico de lecturas en metros cúbicos ($m^3$).
- **Proforma Informativa de Medición (R-DOM-09):** Visualización del consumo mensual con historial comparativo real de hasta 3 lecturas anteriores y aviso obligatorio de no-recibo.
- **Historial de Recibos Oficiales:** Consulta e impresión de comprobantes de caja autorizados (`REC-YYYY-000001`) con código de verificación.
- **Autoservicio de Contacto:** Actualización autónoma de teléfono y correo electrónico sincronizada entre `Socio` y `Usuario`, auditada en `BitacoraAuditoria`. Bloqueo absoluto de operaciones de caja, modificación de lecturas o alteración de datos de identidad desde el portal.

### 8. 008-auditoria-final-puesta-en-marcha (COMPLETADA Y VERIFICADA AL 100% - 6 Tests)
Plan técnico: [specs/008-auditoria-final-puesta-en-marcha/plan.md](specs/008-auditoria-final-puesta-en-marcha/plan.md) | Tasks: [specs/008-auditoria-final-puesta-en-marcha/tasks.md](specs/008-auditoria-final-puesta-en-marcha/tasks.md).
- **Diagnóstico Automatizado de Integridad de Datos (`verificar_integridad_sistema`):** Evaluación integral de las 9 reglas de integridad de la Sección 13 (no duplicidad de CI, asignación exclusiva de medidor, unicidad de lectura mensual, membresía única, cuadratura al 100% de recibos vs detalles, y sanitización estricta de auditoría).
- **Motor de Respaldo Institucional Criptográfico (`backup_institucional`):** Volcado serializado completo de todos los modelos de SisAgua con manifiesto estructurado `manifest.json`, desglose por modelo y checksum SHA-256 para validación de no alteración.
- **Batería de Pruebas de Integración Cruzada de Fin de Ciclo:** Certificación rigurosa de invariantes (prohibición de doble cobro, bloqueo de asignación duplicada de medidores, cero borrado físico y sanitización recursiva de secretos).

---

## Orden Canónico de Fases de Implementación (Sección 15 de la Fuente):
1. [x] **Fase 1:** Configuración institucional, seguridad, usuarios, roles, permisos y menús.
2. [x] **Fase 2:** Datos maestros (zonas, socios, servicios, tarifarios, medidores).
3. [x] **Fase 3:** Consumo y lecturas (captura, validación de anomalías, proforma informativa y motor de facturación).
4. [x] **Fase 4:** Caja, cobros, recibos oficiales, control de turnos y arqueos.
5. [x] **Fase 5:** Transcripción histórica y regularización de deudas (Sección 8 y 15).
6. [x] **Fase 6:** Reportes administrativos, financieros, consumo y padrón (Sección 10).
7. [x] **Fase 7:** Portal individual de socios (consulta de estado de cuenta y proformas, Sección 11).
8. [x] **Fase 8:** Pruebas integrales, auditoría final, exportación y puesta en marcha (Secciones 12 y 13).
