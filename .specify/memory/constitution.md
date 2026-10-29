<!--
SYNC IMPACT REPORT
==================
Constitución Oficial del Sistema de Administración, Consumo y Cobro de Agua Potable (SisAgua).
Sustituye la plantilla genérica del starter SDD.
Basada en el análisis integral del documento fuente primario: "SISTEMA DE ADMINISTRACIÓN.docx" (40 págs., 882 párrafos).

Versión actual: 1.0.0 (Borrador Normativo Oficial para Ratificación Institucional)
Fecha de emisión: Octubre 2026
Jurisdicción: Estado Plurinacional de Bolivia (Marco Ley N° 2066 / AAPS)
Moneda base: Bolivianos (Bs) - DECIMAL(12,2)
Huso horario / Formato: UTC-4 (BOT - Bolivia Time) / DD/MM/AAAA

Principios Fundamentales Integrados (15 Principios P1 a P15 articulados en 9 Ejes SDD):
  - I.    Seguridad, Privacidad y Aislamiento de Datos Primero [P6, P7, P13] (NO NEGOCIABLE)
  - II.   Soberanía / Self-Hosted Comunitario [P11, P14]
  - III.  Aislamiento Institucional / Multi-Tenancy Modular [P2, P13]
  - IV.   Integridad Financiera, Idempotencia y Transaccionalidad ACID [P3, P4, P8] (NO NEGOCIABLE)
  - V.    Calidad Verificable, Validación Previa y Conservación Histórica [P5, P10] (NO NEGOCIABLE)
  - VI.   Specs Antes de Código y Fidelidad de Negocio [P1, P15]
  - VII.  Trazabilidad de Decisiones y Doble Carril de Migración [P6, P8]
  - VIII. Foco Vertical: Gestión Integral de Agua Potable Comunitaria en Bolivia
  - IX.   Verificación de Comportamiento en Vivo y Fronteras Tarifarias [P3, P12] (NO NEGOCIABLE)

Bloqueos Críticos Pre-Producción:
  - D-01: Discontinuidad tarifaria en consumos > 15 m³ (caída de Bs 27 a Bs 20).
  - D-02: Importe no definido y tratamiento de exención de membresías históricas.
  - D-08: Régimen fiscal del recibo (Recibo Oficial Comunitario vs. Factura SIAT).
  - D-10: Protocolo de activación de deudas históricas transcritas.
  - D-15: Ratificación de stack definitivo (PostgreSQL + Framework desacoplado).
-->

# SisAgua — Constitución del Sistema de Agua Potable

SisAgua es el sistema centralizado de administración, micro-medición, facturación por consumo y cobranza de agua potable para comités, cooperativas y asociaciones comunitarias en Bolivia. Esta constitución define las reglas supremas, innegociables y rectoras del producto. Gobierna todas las fases del ciclo SDD (specify, clarify, plan, tasks, implement). Cualquier conflicto entre una decisión de desarrollo y esta constitución **SE RESUELVE A FAVOR DE ESTA CONSTITUCIÓN**.

> **CONDICIÓN DE BLOQUEO DE FACTURACIÓN:**  
> Esta Constitución no autoriza la emisión de cobros reales ni la puesta en producción mientras persistan sin ratificación formal las Decisiones Bloqueantes registradas en [.specify/memory/pending-decisions.md](pending-decisions.md) (especialmente **D-01: Tarifa > 15 m³** y **D-02: Membresía**).

---

## Core Principles

### I. Seguridad, Privacidad y Aislamiento de Datos Primero (NO NEGOCIABLE) [P6, P7, P13]

La protección de los datos personales de los socios y la integridad de las credenciales prevalece sobre la velocidad de entrega o la conveniencia técnica.

- **Prohibición del Carnet como Clave Permanente:** Bajo ninguna circunstancia se utilizará el número de Documento de Identidad (CI) como contraseña permanente de acceso al portal. En caso de usarse en el enrolamiento inicial, tendrá condición de contraseña temporal de un solo uso con forzado de cambio en el primer inicio de sesión.
- **Criptografía de Contraseñas:** Se exige el almacenamiento seguro de contraseñas mediante **Argon2id** (preferente) o **bcrypt** (costo $\ge 12$). Queda prohibido MD5, SHA1 o texto en claro.
- **Aislamiento Horizontal Estricto:** Cada socio solo puede acceder a su propia información de consumo, deudas y recibos. Se aplicará autorización obligatoria basada en propiedad del recurso (*Owner-based Authorization*) en servidor para evitar vulnerabilidades de referencia directa insegura (IDOR).
- **Protección de Secretos y Auditoría Limpia:** Secretos, tokens y contraseñas jamás se exponen en APIs, logs de consola ni en las tablas de auditoría.
- **Defensa en Profundidad:** Parametrización total de consultas SQL (prohibición de concatenación de cadenas), sanitización contra XSS y tokens CSRF en formularios mutantes.

### II. Soberanía / Self-Hosted Comunitario [P11, P14]

El sistema debe operar de forma autónoma sobre infraestructura local o servidores virtuales privados (VPS) controlados por la organización, minimizando la dependencia de servicios propietarios externos.

- El núcleo transaccional (Base de Datos Relacional y Backend) correrá sobre infraestructura controlada.
- Las funciones operativas de oficina (captura de lecturas, emisión de proformas, cobro en caja y emisión de recibos) no dependerán de APIs SaaS de terceros para su funcionamiento regular.
- La arquitectura mantendrá una separación estricta entre la interfaz de usuario, los servicios de dominio financiero y la capa de persistencia de datos.

### III. Aislamiento Institucional / Multi-Tenancy Modular [P2, P13]

El sistema se diseña con aislamiento institucional garantizado. Si bien el despliegue prioritario en el MVP es de instancia única (*Single-Tenant*), el modelo de datos incorporará identificadores institucionales que permitan la transición a *Multi-Tenant* sin reescritura del dominio.

- Cada organización administra de manera autónoma sus zonas, tarifas, padrón de socios, usuarios y permisos.
- No existirá contaminación cruzada de datos, parámetros o numeraciones de recibos entre diferentes comités.

### IV. Integridad Financiera, Idempotencia y Transaccionalidad ACID (NO NEGOCIABLE) [P3, P4, P8]

Toda operación monetaria y de afectación de cuentas por cobrar debe ser matemáticamente exacta, atómica e indivisible.

- **Prohibición Absoluta de Pagos Parciales:** No se permiten abonos parciales sobre el saldo de una obligación individual. Cada obligación seleccionada se liquida por el 100% de su monto.
- **Cobro Atómico en Caja:** La confirmación de cobro, la actualización de las obligaciones a estado `Pagada`, la inserción del pago y la asignación del correlativo de recibo se ejecutan dentro de una única transacción atómica ACID (`BEGIN ... COMMIT`). Si ocurre cualquier fallo, se ejecuta un *rollback* completo sin efectos colaterales.
- **Idempotencia Absoluta:** La repetición intencional o accidental de una solicitud (por caída de red o dobles clics) jamás duplicará lecturas, obligaciones, membresías, cobros ni recibos.
- **Bloqueo Concurrente:** El módulo de caja aplicará bloqueos pesimistas (`FOR UPDATE`) sobre las obligaciones seleccionadas para evitar que dos cajeros o procesos cobren la misma deuda en paralelo.
- **Transparencia Financiera:** Se mantendrá una distinción contable y visual inalterable entre: importe calculado teóricamente, importe histórico documentado en papeles físicos, importe facturado, importe efectivamente cobrado, saldo pendiente y conceptos anulados.

### V. Calidad Verificable, Validación Previa y Conservación Histórica (NO NEGOCIABLE) [P5, P10]

Ningún dato dudoso afectará las finanzas y ningún registro histórico será destruido.

- **Prohibición de Borrado Físico:** Se prohíbe el uso de sentencias `DELETE` en tablas operativas y transaccionales (socios, medidores, lecturas, obligaciones, pagos, recibos, auditoría). Toda baja, inactivación o anulación se gestionará mediante estados lógicos y transacciones compensatorias.
- **Validación Previa:** Una lectura observada (consumo negativo, salto anómalo) o una deuda histórica sin respaldo suficiente jamás generará automáticamente una obligación cobrable en la cuenta del socio.
- **Inalterabilidad del Recibo:** El recibo emitido es inmutable. Su anulación exige supervisor autorizado, justificación obligatoria, registro en auditoría y reversión lógica automática que restablece las obligaciones a estado `Pendiente`.

### VI. Specs Antes de Código y Fidelidad de Negocio [P1, P15]

Ninguna funcionalidad o componente se implementa sin su correspondiente especificación SDD previa.

- **Fidelidad de Negocio:** Ninguna regla financiera o tarifaria se modifica sin aprobación formal documentada de la Asamblea o Directorio. Los desarrolladores no pueden alterar fórmulas por criterio propio.
- **Ciclo Obligatorio:** El desarrollo sigue la secuencia estricta: `specify → clarify → plan → tasks → analyze → implement`.
- **Gobernanza Constitucional:** Toda desviación o enmienda a esta Constitución exige un proceso formal de RFC con evaluación de impacto y aprobación colegiada unánime.

### VII. Trazabilidad de Decisiones y Doble Carril de Migración [P6, P8]

Toda operación histórica y actual debe ser completamente auditable y verificable.

- **Pista de Auditoría Obligatoria:** Cada acción sensible (altas, modificaciones, cobranzas, anulaciones, validaciones de migración) registra automáticamente: ID del usuario, dirección IP, timestamp UTC, entidad afectada, valor previo, valor modificado y motivo.
- **Principio del Doble Carril en Migración:** La transcripción de lecturas históricas pertenece al carril de análisis de consumo. No genera una deuda exigible en caja hasta que cumpla con el carril de regularización: validación contra documento de respaldo físico y autorización administrativa.
- **Ciclo de Transcripción en 6 Estados:** `Pendiente → Transcrito → Observado → Validado → Migrado / Rechazado`. Un registro transcrito no se considera migrado hasta que un supervisor lo valide formalmente.

### VIII. Foco Vertical: Gestión de Agua Potable Comunitaria (Bolivia)

SisAgua sirve exclusivamente a **Comités de Agua Potable y Saneamiento (CAPYS), Cooperativas de Servicios Públicos y Asociaciones Comunitarias de Agua** en el contexto boliviano.

- **Modelo de Dominio Específico:** El modelo de datos refleja el dominio de agua comunitario: Socio (titular), Predio/Inmueble (ubicación en zona), Medidor (activo físico con lecturas acumuladas en $\text{m}^3$), Obligación Mensual de Consumo y Membresía/Afiliación.
- **Membresía como Concepto Independiente:** La membresía es un concepto único de afiliación patrimonial o derecho de conexión, generado al dar de alta al socio, aislado del consumo y no recurrente mensualmente.
- **Contexto Regulatorio Local:** El sistema reconoce las directrices de la AAPS y la Ley N° 2066. En su fase inicial emite el Recibo Oficial de Cobranza Comunitario (no fiscal), manteniendo desacoplada la potencial integración con facturación electrónica SIAT.

### IX. Verificación de Comportamiento en Vivo y Fronteras Tarifarias (NO NEGOCIABLE) [P3, P12]

Toda feature con comportamiento observable debe verificarse de punta a punta antes de considerarse terminada.

- **Pruebas de Frontera Tarifaria:** El motor de cálculo debe validarse exhaustivamente contra los valores límite: $0, 9, 10, 12, 14, 15, 16 \text{ y } 50 \text{ m}^3$, certificando el cálculo exacto de cada tramo y el manejo de consumos nulos.
- **Self-Test E2E por el Implementador:** Tras implementar una feature, quien programa conduce el flujo real (navegador / llamadas a servicio), cubriendo el camino feliz y el camino infeliz (degradación controlada sin colgarse), antes de marcar la tarea como completada.
- **Usabilidad Human-Centered:** Interfaces adaptables (Responsive / PWA), diseñadas para PC de escritorio, tabletas y teléfonos celulares en campo, con confirmación previa a cualquier acción financiera irreversible.

---

## Restricciones de Plataforma y Seguridad

1.  **Motor de Base de Datos:** Relacional con cumplimiento ACID pleno y soporte estricto de transacciones concurrentes (PostgreSQL recomendado).
2.  **Manejo de Moneda:** Tipos de datos numéricos exactos (`DECIMAL(12,2)` o `NUMERIC(12,2)`), prohibiendo tipos de coma flotante (`FLOAT/DOUBLE`) en cálculos financieros.
3.  **Control de Acceso Basado en Roles (RBAC):** Validación de permisos ejecutada forzosamente en el servidor en cada petición. Ocultar menús o botones en la interfaz no constituye control de acceso.
4.  **Políticas de Respaldo:** Copia de seguridad automatizada diaria; retención de 30 días locales y respaldo mensual fuera del sitio; simulacro trimestral de restauración verificado.

---

## Flujo de Trabajo y Puertas de Calidad SDD

```
specify → clarify → plan → tasks → analyze → implement
```

1.  **Constitution Check (Puerta Constitucional):** Todo plan de feature evalúa su conformidad con esta Constitución antes de descomponerse en tareas. Cualquier conflicto con los Principios I a IX detiene la feature hasta su alineación.
2.  **Definición de "Hecho" (Definition of Done):**
    - Verificación técnica: tipado estricto + linter sin errores + build exitoso + pruebas unitarias de dominio financiero.
    - Verificación en vivo: prueba funcional de punta a punta del comportamiento observable.
    - Auditoría: verificación de que no existen sentencias `DELETE` en tablas de dominio ni secretos en texto claro.

---

## Documentos de Respaldo y Memoria Durable

Para el detalle integral de especificaciones, análisis y matrices que sustentan esta Constitución, consultar los archivos correspondientes en `.specify/memory/` y en la raíz del proyecto:

*   [CONSTITUCION_SDD_v1.0.md](../../CONSTITUCION_SDD_v1.0.md) — Documento maestro completo consolidado (100k caracteres).
*   [pending-decisions.md](pending-decisions.md) — Registro formal de Decisiones Pendientes (D-01 a D-20).
*   [traceability-matrix.md](traceability-matrix.md) — Matriz de trazabilidad cruzada (Fuente $\leftrightarrow$ Principios $\leftrightarrow$ Módulos $\leftrightarrow$ Criterios).
*   [benchmark.md](benchmark.md) — Benchmark comparativo de sistemas de agua en Bolivia y Latinoamérica.
*   [blockers-checklist.md](blockers-checklist.md) — Lista de comprobación y acta de bloqueos para el Directorio y Asamblea.

---

**Version**: 1.0.0 | **Status**: BORRADOR NORMATIVO EN REVISIÓN | **Ratified**: Pendiente de Asamblea/Directorio
