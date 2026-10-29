# -*- coding: utf-8 -*-
"""
PARTE E: BENCHMARK DE SISTEMAS EXISTENTES Y ANÁLISIS COMPARATIVO
"""

def get_part_e():
    return """
# PARTE E. BENCHMARK DE SISTEMAS EXISTENTES Y ANÁLISIS COMPARATIVO

Para enriquecer la arquitectura de **SisAgua** y contextualizar sus decisiones operativas y normativas, se realizó un análisis comparativo frente a soluciones existentes en el ámbito de la gestión comunitaria, cooperativa y municipal de agua potable en Bolivia y América Latina.

---

## E.1. Soluciones Evaluadas

1.  **Sistemas Comerciales de EPSAs Grandes y Medianas en Bolivia (EPSAS La Paz/El Alto, SAGUAPAC Santa Cruz, SEMAPA Cochabamba):**
    *   *Descripción:* Sistemas empresariales centralizados (frecuentemente desarrollados sobre SAP, Oracle o plataformas a medida en Java/.NET).
    *   *Enfoque:* Operación a gran escala (>100,000 conexiones), facturación electrónica SIAT obligatoria, cuadrillas de toma de lecturas con terminales móviles dedicadas, contabilidad de partida doble integrada y gestión de macro/micro medición.
    *   *Referencia:* Portal de la [AAPS - Autoridad de Fiscalización y Control Social de Agua Potable y Saneamiento Básico](https://www.aaps.gob.bo) y regulaciones del marco de la [Ley N° 2066 de Servicios de Agua Potable y Alcantarillado Sanitario](https://www.lexivox.org/norms/BO-L-2066.html).

2.  **Sistemas de Cooperativas Periurbanas y Rurales en Bolivia (COSCHAL, COOPAPLAN, CAPYS):**
    *   *Descripción:* Software administrativo local (generalmente desarrollado en PHP/MySQL, Visual FoxPro o macros avanzadas de Excel con base de datos Access).
    *   *Enfoque:* Gestión de 500 a 10,000 socios, cobranza directa en ventanilla comunal, emisión de "Recibos Oficiales de Cobranza de Agua" (no fiscales), control de aportes comunales, faenas y asambleas.
    *   *Limitaciones habituales:* Dependencia de un único desarrollador local, alta vulnerabilidad a pérdidas de datos por falta de respaldos automáticos, ausencia de pistas de auditoría y mezcla entre la titularidad del medidor y el inmueble.

3.  **Plataformas Internacionales de Gestión de Agua Comunitaria y Monitoreo (mWater, WaterAdmin, SISAR Brasil):**
    *   *mWater Suite:* Plataforma global abierta utilizada en más de 180 países para el monitoreo de infraestructura de agua, calidad y lectura de medidores móviles con capacidades offline y captura fotográfica. ([mWater Portal](https://www.mwater.co)).
    *   *WaterAdmin / WatERP:* Soluciones basadas en software libre para pequeñas asociaciones de agua potable, orientadas al cálculo de tarifas escalonadas y control de cobranza en comunidades rurales de América Latina.
    *   *Modelo SISAR (Ceará, Brasil):* Sistema Integrado de Saneamiento Rural, referente latinoamericano en gestión federada de cientos de asociaciones comunitarias de agua con plataforma centralizada de facturación y soporte técnico.

---

## E.2. Matriz Comparativa de Capacidades

| Capacidad / Función | EPSAs Grandes (SAGUAPAC / EPSAS) | Cooperativas Bolivianas (COSCHAL / CAPYS) | Plataformas Abiertas (mWater / WaterAdmin) | SisAgua (Constitución SDD v1.0) | Estado en SisAgua |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cálculo Tarifario por Tramos** | Continuo, creciente y penalizador del derroche | Tramos simples o cuota fija; frecuentes anomalías locales | Tramos configurables estándar (lineales crecientes) | Regla fuente original (con anomalía > 15 m³ bajo bloqueo) | **Propuesta bajo Decisión D-01** |
| **Gestión de Membresías / Acciones** | Acciones patrimoniales transables en cooperativas | Pago único de afiliación / derecho de conexión comunal | No contempla membresías comunitarias (solo servicio) | Concepto independiente, pago único, no recurrente | **Publicada y Protegida (P1, P4)** |
| **Pagos Parciales** | Permitidos (abonos a cuenta o pago en cuotas) | Estrictamente prohibidos en la mayoría de comités | Soportados en módulos de cuentas por cobrar | Estrictamente prohibidos por obligación | **Publicada y Protegida (P3, P8)** |
| **Toma de Lecturas en Campo** | Terminales móviles con GPS y foto obligatoria | Cuaderno manuscrito o planilla de papel impresa | App móvil offline con captura fotográfica | Web responsive (PWA) móvil + Planilla de contingencia | **Propuesta (D-16)** |
| **Proforma Informativa de Medición** | Pre-aviso de cobranza impreso en ruta en papel térmico | No siempre se entrega; aviso verbal o pizarra comunal | Notificación digital o proforma informativa | Proforma informativa oficial con historial de 3 meses | **Publicada y Protegida (REQ-16)** |
| **Migración de Archivos Históricos** | Migraciones masivas mediante scripts ETL en BD | Transcripción manual informal sin estados de control | Importación masiva por hojas de cálculo CSV | Módulo formal de 6 estados con doble carril (consumo vs deuda) | **Innovación Central SisAgua** |
| **Portal Autónomo del Socio** | Web y App móvil nativa con pago QR / Pasarela | Inexistente (atención 100% presencial en sede) | Portal web básico | Portal web responsive con aislamiento horizontal estricto | **Publicada (Módulo 10)** |
| **Facturación Fiscal Electrónica** | SIAT en Línea obligatorio (SIN Bolivia) | Recibo Oficial Interno Comunitario (exento AAPS) | Sin integración fiscal boliviana | Recibo Interno Comunitario (SIAT fuera de MVP) | **Validación Legal (D-08)** |
| **Auditoría e Integridad Transaccional** | Logs de auditoría empresarial y replicación en caliente | Bitácoras inexistentes; borrado físico frecuente en BD | Logs de base de datos estándar | Bitácora inalterable, RBAC estricto, sin DELETE físico | **Publicada y Protegida (P5, P6)** |

---

## E.3. Clasificación Normativa de Capacidades para SisAgua

Para preservar la disciplina de SDD, se clasifica el comportamiento de SisAgua en tres categorías formales:

### 1. Funciones Publicadas (Aprobadas en el Documento Fuente)
*   Cálculo de consumo mensual por diferencia de lecturas válidas ($C = L_{act} - L_{ant}$).
*   Prohibición absoluta de pagos parciales sobre una obligación.
*   Emisión de Recibo de Pago Oficial e inalterable, con anulación lógica auditada.
*   Membresía como concepto independiente de pago único al registrar un nuevo socio.
*   Multi-medidor por socio y consolidación de deudas pendientes.
*   Proforma informativa de lectura con comparación de hasta 3 periodos anteriores disponibles.
*   Módulo de transcripción histórica con estados de revisión (`Pendiente`, `Transcrito`, `Observado`, `Validado`, `Migrado`, `Rechazado`).
*   Principio del doble carril: una lectura histórica no genera automáticamente una deuda exigible.
*   Portal del socio con consulta de medidores, consumos, deudas y descarga de recibos propios.

### 2. Funciones Propuestas (Mejoras Basadas en el Benchmark)
*   **Captura Móvil con PWA y Fotografía (Inspirada en mWater):** Habilitar una vista ligera para smartphones que permita al lector en campo tomar una fotografía del cuadrante del medidor como respaldo irrevocable ante reclamos por consumo anómalo (**D-16**).
*   **Monotonía y Tarifas Incrementales (Inspirada en AAPS/EPSAS):** Proponer formalmente a la Asamblea la adopción de una fórmula tarifaria continua que elimine la reducción a Bs 20 para consumos superiores a 15 m³, protegiendo el recurso hídrico (**D-01**).
*   **Prelación de Cobro FIFO (Inspirada en cooperativas formales):** Exigir al cajero la cancelación obligatoria de la obligación más antigua vencida para evitar la prescripción de deudas y la discrecionalidad en ventanilla (**D-05**).
*   **Enrolamiento Seguro por Talón Impreso:** Entrega física de credenciales iniciales con código QR de acceso y forzado de cambio de clave en el primer ingreso (**D-13**).

### 3. Funciones que Aún Deben Validarse (Condicionadas a Decisión Institucional)
*   **Régimen Tributario del Recibo:** Validación con el asesor contable de la personería jurídica ante el SIN (Recibo interno comunitario vs. Facturación SIAT) (**D-08**).
*   **Horizonte de Migración Histórica:** Aprobación del Directorio sobre qué gestiones del pasado serán digitalizadas y cuáles quedarán archivadas físicamente (**D-09**).
*   **Cuantía de la Membresía:** Fijación del valor oficial en bolivianos por asamblea de socios (**D-02**).
*   **Manejo de Inmuebles y Traspasos:** Confirmación del modelo estructural integral Socio-Predio-Medidor (**D-11**).
"""

