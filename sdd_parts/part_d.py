# -*- coding: utf-8 -*-
"""
PARTE D: MATRIZ DE TRAZABILIDAD CRUZADA
"""

def get_part_d():
    return """
# PARTE D. MATRIZ DE TRAZABILIDAD CRUZADA

La siguiente matriz establece el hilo conductor inviolable de **Spec-Driven Development (SDD)**, vinculando cada requerimiento con su respaldo en el documento fuente, su principio constitucional rector, el módulo ejecutor y su criterio de verificación formal:

| ID Req. | Sección y Párrafos Fuente | Descripción del Requisito Normativo | Categoría | Principio Rector | Módulo Afectado | Criterio de Aceptación Verificable |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Sec. 2.1 (P20-P48) | Cálculo tarifario según tramos vigentes y no retroactividad | **[A]** | **P1, P9** | Módulo 3 / Módulo 5 | Verificación matemática exacta en $0, 9, 10, 12, 14, 15, 16 \\text{ m}^3$ sin afectar recibos pasados. |
| **REQ-02** | Sec. 2.2 (P49-P58) | Consumo = Lectura Actual - Lectura Anterior válida | **[A]** | **P2, P10** | Módulo 4 / Módulo 5 | Rechazo automático de lecturas inferiores sin flujo de regularización justificada. |
| **REQ-03** | Sec. 2.3 (P59-P66) | Vencimiento unificado con corrimiento a fin de mes | **[A]** | **P2, P9** | Módulo 5 | Determinación automática de estado `Vencida` tras superar el día configurado o último de mes. |
| **REQ-04** | Sec. 2.4 (P67-P71) | Prohibición absoluta de pagos parciales por obligación | **[A]** | **P3, P8** | Módulo 7 | Imposibilidad de registrar cobros fraccionados o recibos con saldos residuales. |
| **REQ-05** | Sec. 2.5 (P72-P76) | Múltiples medidores por socio y unicidad de cuenta | **[A]** | **P2, P14** | Módulo 2 | Un socio acumula deudas de varios medidores; ningún medidor se asigna a 2 contratos activos concurrentes. |
| **REQ-06** | Sec. 2.6 (P77-P89) | Membresía única, independiente y no recurrente | **[A]** | **P1, P4** | Módulo 6 | Generación automática por única vez al dar de alta al socio; bloqueo de generación mensual. |
| **REQ-07** | Sec. 3.2 (P136-P148) | Parametrización institucional en base de datos sin tocar código | **[A]** | **P9, P14** | Módulo 1 | Actualización de nombre, logo, moneda y teléfonos desde interfaz con reflejo inmediato en recibos. |
| **REQ-08** | Sec. 3.3 (P149-P160) | Administración dinámica de menús y protección en backend | **[A]** | **P7, P14** | Módulo 1 | Enlaces ocultos en menú siguen inaccesibles mediante HTTP directo si el rol carece de permiso. |
| **REQ-09** | Sec. 3.4 (P161-P185) | Matriz granular de roles y permisos verificada en servidor | **[A]** | **P6, P7** | Módulo 1 | Verificación por token/sesión en cada endpoint de API y acción mutante en el backend. |
| **REQ-10** | Sec. 4.1 (P197-P214) | Gestión de zonas y prohibición de borrado con dependencias | **[A]** | **P5, P14** | Módulo 2 | Bloqueo de eliminación física de zonas con medidores o socios activos asociados. |
| **REQ-11** | Sec. 5.1 (P216-P237) | Catálogo de servicios con distintas modalidades de cobro | **[A]** | **P8, P9** | Módulo 2 / Módulo 3 | Soporte para consumo volumétrico, cuotas fijas mensuales y derechos de cobro único. |
| **REQ-12** | Sec. 5.2 (P238-P265) | Historial de titularidad, retiro y reemplazo de medidores | **[A]** | **P5, P6** | Módulo 2 | Preservación de lecturas del medidor retirado y registro de lectura inicial del nuevo. |
| **REQ-13** | Sec. 6.1 (P283-P299) | Código único de socio y control estricto de duplicidad de CI | **[A]** | **P2, P7** | Módulo 2 | Restricción de unicidad (`UNIQUE`) en base de datos sobre el número de documento de identidad. |
| **REQ-14** | Sec. 6.3 (P322-P335) | Transaccionalidad atómica en el alta de socio y membresía | **[A]** | **P3, P4** | Módulo 2 / Módulo 6 | Si falla la creación de la membresía, el socio no se persiste en base de datos (*Rollback* total). |
| **REQ-15** | Sec. 6.4 (P336-P343) | Independencia de estado del socio y vigencia de su deuda | **[A]** | **P5, P8** | Módulo 2 / Módulo 7 | Un socio `Inactivo` o `Retirado` sigue figurando en reportes de deudores hasta saldar su cuenta. |
| **REQ-16** | Sec. 7.1-7.3 (P374-413)| Captura mensual, proforma informativa y lecturas observadas | **[A]** | **P2, P10** | Módulo 4 | Lecturas con consumos anómalos o negativos quedan congeladas en `Observada` para auditoría. |
| **REQ-17** | Sec. 7.5 (P431-P443) | Idempotencia en la generación masiva de obligaciones | **[A]** | **P3, P4** | Módulo 5 | Ejecutar dos veces el proceso mensual no genera deudas repetidas para el mismo periodo y medidor. |
| **REQ-18** | Sec. 8.1-8.6 (P444-535)| Transcripción histórica en 6 estados con reporte auditable | **[A]** | **P6, P8** | Módulo 8 / Módulo 9 | Trazabilidad del transcriptor, supervisor, fecha y avance de migración exportable a PDF/Excel. |
| **REQ-19** | Sec. 8.7 (P536-P548) | Doble carril: desacoplamiento entre lectura y deuda histórica | **[A]** | **P8, P10** | Módulo 8 / Módulo 5 | Ninguna lectura transcrita genera deuda en caja sin validación y acta de regularización. |
| **REQ-20** | Sec. 9.1-9.3 (P552-596)| Cobranza atómica en caja, selección múltiple y bloqueo concurrente| **[A]** | **P3, P4** | Módulo 7 | Bloqueo pesimista de obligaciones al momento de cobro; liquidación total sin cobros duplicados. |
| **REQ-21** | Sec. 9.4 (P597-P613) | Recibo oficial inalterable con anulación lógica y reversión | **[A]** | **P5, P6** | Módulo 7 | La anulación de recibo requiere justificación, no borra el registro y reactiva la deuda en `Pendiente`. |
| **REQ-22** | Sec. 9.5 (P614-P623) | Control de caja, apertura, cierre y arqueo con diferencias | **[A]** | **P3, P6** | Módulo 7 | Registro ciego de arqueo y reporte de sobrantes/faltantes por cajero y fecha. |
| **REQ-23** | Sec. 10.1-10.7 | Reportes consolidados de deudores, consumo, caja y migración | **[A]** | **P2, P8** | Módulo 9 | Conciliación matemática exacta: lo recaudado coincide con la suma de recibos activos emitidos. |
| **REQ-24** | Sec. 11 (P724-P739) | Portal individual del socio con aislamiento horizontal estricto | **[A]** | **P7, P13** | Módulo 10 | Un socio autenticado no puede acceder a consumos ni recibos de otros usuarios cambiando el ID. |
| **REQ-25** | Sec. 12.1-12.2 | Prohibición de CI como clave permanente y hashing robusto | **[A]** | **P7, P13** | Módulo 1 / Módulo 10| Almacenamiento seguro con Argon2id/bcrypt y forzado de cambio de clave en el primer acceso. |
| **REQ-26** | Sec. 12.3 (P756-P770) | Pista de auditoría inalterable libre de secretos o tokens | **[A]** | **P6, P7** | Módulo 11 | Bitácora de eventos con usuario, IP, timestamp, entidad y detalle, sin registrar contraseñas. |
| **REQ-27** | Sec. 14 (P785-P799) | Arquitectura MVC/Clean desacoplada con transacciones ACID | **[B]** | **P3, P14** | Toda la Arquitectura | Separación de capas comprobada en pruebas unitarias de servicios de dominio sin base de datos. |
| **REQ-28** | Sec. 15 (P800-P846) | Despliegue en 7 fases respetando dependencias funcionales | **[B]** | **P15** | Plan de Proyecto | Prohibición de avanzar a caja sin datos maestros ni motor de consumo debidamente certificados. |
| **REQ-29** | Sec. 17 (P863-P877) | Registro y resolución de Decisiones Pendientes Bloqueantes | **[B]** | **P1, P15** | Gobernanza | Bloqueo de facturación productiva mientras persistan decisiones críticas sin ratificar (D-01, D-02). |
"""

