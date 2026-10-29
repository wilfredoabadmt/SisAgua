# -*- coding: utf-8 -*-
"""
PARTE B: CONSTITUCIÓN SDD v1.0 DEL PROYECTO SISAGUA
"""

def get_part_b():
    return """
# PARTE B. CONSTITUCIÓN SDD v1.0 DEL SISTEMA DE ADMINISTRACIÓN, CONSUMO Y COBRO DE AGUA POTABLE (SisAgua)

## B.1. Preámbulo, Propósito y Misión Normativa

La presente **Constitución del Proyecto** constituye la norma fundacional, suprema e inmutable para el diseño, desarrollo, pruebas, migración, despliegue y evolución del **Sistema de Administración, Consumo y Cobro de Agua Potable (SisAgua)**. Bajo el paradigma de **Spec-Driven Development (SDD)**, esta Constitución establece las directrices arquitectónicas, los principios ontológicos, los límites funcionales y las salvaguardas éticas y financieras que subordinan a toda especificación posterior, decisión técnica o línea de código.

### Misión del Sistema
Proveer a comités, cooperativas, juntas administradoras y asociaciones de agua potable una plataforma tecnológica integral, transparente, auditable y de alta confiabilidad que erradique la dependencia de registros manuscritos y planillas aisladas; automatice con precisión matemática el cálculo de consumos y cobros; garantice la integridad transaccional de los fondos recaudados; preserve la memoria histórica de la comunidad; y empodere a los socios mediante el acceso oportuno y fidedigno a su información de servicio.

### Visión Arquitectónica
Consolidar una arquitectura desacoplada, modular, escalable y resiliente, diseñada para operar con excelencia tanto en entornos urbanos consolidados como en contextos periurbanos y rurales con conectividad intermitente, gobernada por principios estrictos de neutralidad tecnológica, trazabilidad absoluta y privilegio mínimo.

---

## B.2. Contexto Institucional, Geográfico y Operativo

1.  **Marco Territorial y Societario:** El sistema está concebido para organizaciones comunitarias de agua en el **Estado Plurinacional de Bolivia** (Comités de Agua Potable y Saneamiento - CAPYS, Cooperativas de Servicios Públicos y Asociaciones de Usuarios), regidas por los principios comunitarios de autoabastecimiento, fiscalización colectiva y ausencia de lucro usurario, en el marco de la **Ley N° 2066** y los estándares regulatorios de la **AAPS** (Autoridad de Fiscalización y Control Social de Agua Potable y Saneamiento Básico).
2.  **Moneda Base:** La moneda oficial, única e indivisible para toda operación contable, tarifaria y de cobranza es el **Boliviano (Bs)**. Todas las transacciones monetarias se calcularán y registrarán con precisión de dos (2) decimales (`DECIMAL(12, 2)`), salvo las reglas explícitas de redondeo que ratifique la organización.
3.  **Huso Horario y Metrología Temporal:** Toda marca temporal (*timestamp*) se registrará de forma nativa en tiempo universal coordinado (UTC) y se proyectará para presentación en el huso oficial de Bolivia: **UTC-4 (BOT - Bolivia Time)**. El formato visual estandarizado e inequívoco para fechas es estrictamente **DD/MM/AAAA** y para horas **HH:MM:SS (24 horas)**.
4.  **Idioma de Operación:** Toda la interfaz de usuario, proformas, recibos, reportes oficiales, mensajes del sistema y documentación técnica se redactarán en **español neutro formal**.

---

## B.3. Objetivos del Sistema

### Objetivos Estratégicos
*   **OE-1. Transparencia y Rendición de Cuentas:** Proporcionar estados financieros y de recaudación exactos y verificables, eliminando la opacidad en el manejo de fondos comunitarios y facilitando auditorías internas y externas.
*   **OE-2. Sostenibilidad del Servicio:** Asegurar una cobranza equitativa y puntual basada en el consumo real medido, protegiendo la viabilidad financiera de la organización prestadora.
*   **OE-3. Memoria Institucional:** Salvaguardar el patrimonio histórico de la comunidad mediante la migración controlada y validada de libros de lectura y deudas históricas sin riesgo de adulteración.

### Objetivos Operativos
*   **OO-1. Erradicación de Errores de Transcripción:** Automatizar la diferencia de lecturas, el cálculo de tramos tarifarios y la generación de obligaciones mensuales.
*   **OO-2. Control de Caja y Prevención de Fugas:** Blindar las operaciones de cobro mediante recibos únicos, inalterables y con transacciones atómicas que impidan desvíos, cobros no registrados o recibos duplicados.
*   **OO-3. Empoderamiento del Socio:** Disponer de un canal de consulta autónomo (Portal del Socio) que reduzca las colas y reclamos en oficinas administrativas.

---

## B.4. Alcance Funcional Oficial (Los 12 Módulos Esenciales)

Conforme a la estructura canónica del documento fuente, el sistema se compone de doce (12) módulos interdependientes:

```mermaid
flowchart TD
    M01["1. Parametrización, Usuarios y Seguridad"] --> M02["2. Zonas, Socios, Servicios y Medidores"]
    M01 --> M03["3. Tarifarios, Vigencias y Cobros"]
    M02 --> M04["4. Registro y Validación de Lecturas"]
    M03 --> M05["5. Cálculo de Consumo y Obligaciones"]
    M04 --> M05
    M02 --> M06["6. Membresías Independientes"]
    M05 --> M07["7. Caja, Cobros, Recibos y Turnos"]
    M06 --> M07
    M02 --> M08["8. Transcripción y Migración Histórica"]
    M08 -.-> M05
    M07 --> M09["9. Reportes y Estados Financieros"]
    M07 --> M10["10. Portal Autónomo del Socio"]
    M01 --> M11["11. Auditoría, Respaldos y Restauración"]
    M01 --> M12["12. Pruebas, Aceptación y Despliegue"]
```

1.  **Módulo 1: Configuración Institucional, Usuarios, Roles, Permisos y Menús (Sección 3.2, 3.3, 3.4, 3.5, 12):**
    *   *Propósito:* Administrar los parámetros de la entidad (nombre, logotipo, teléfonos, dirección, NIT/personería), la navegación dinámica por perfiles y la matriz de control de acceso basada en roles (RBAC) con verificación estricta en servidor.
2.  **Módulo 2: Gestión de Zonas, Socios, Servicios y Medidores (Sección 4.1, 5.1, 5.2, 6.1 a 6.7):**
    *   *Propósito:* Administrar el padrón societario, las zonas geográficas, el catálogo de servicios (agua potable, recojo de basura, etc.) y el parque de medidores, garantizando unicidad de documento de identidad y control estricto de titularidad/asignación.
3.  **Módulo 3: Tarifarios, Vigencias y Reglas de Cobro (Sección 2.1, 5.3):**
    *   *Propósito:* Configurar y versionar las tablas tarifarias (básica, excedentes, cargos fijos) con fechas de vigencia explícitas, impidiendo retroactividad sobre obligaciones previamente emitidas.
4.  **Módulo 4: Registro y Validación de Lecturas (Sección 7.1, 7.2, 7.3, 7.4):**
    *   *Propósito:* Capturar las lecturas mensuales por medidor, aplicar validaciones matemáticas en tiempo real (consumos negativos, saltos anómalos, medidores sin lectura) y emitir la Proforma Informativa de Lectura.
5.  **Módulo 5: Cálculo de Consumo y Generación de Obligaciones (Sección 2.2, 2.3, 7.5):**
    *   *Propósito:* Procesar en lote o individualmente las lecturas validadas, aplicar la fórmula tarifaria vigente, computar el vencimiento institucional y emitir obligaciones con idempotencia absoluta.
6.  **Módulo 6: Membresías como Concepto Independiente (Sección 2.6, 6.3):**
    *   *Propósito:* Generar de forma atómica y por única vez la obligación de membresía/afiliación al dar de alta a un nuevo socio, garantizando su aislamiento respecto al consumo mensual recurrente.
7.  **Módulo 7: Caja, Cobros, Recibos y Anulaciones Autorizadas (Sección 2.4, 9.1 a 9.5):**
    *   *Propósito:* Gestionar la recaudación en ventanilla, validar la liquidación total de obligaciones seleccionadas (prohibición estricta de pagos parciales), emitir recibos oficiales correlativos, administrar aperturas/cierres/arqueos de caja y procesar anulaciones lógicas auditadas.
8.  **Módulo 8: Transcripción de Lecturas Históricas y Regularización de Deudas (Sección 8.1 a 8.7):**
    *   *Propósito:* Digitalizar planillas y cuadernos antiguos mediante un flujo de seis estados (Pendiente $\\rightarrow$ Transcrito $\\rightarrow$ Observado $\\rightarrow$ Validado $\\rightarrow$ Migrado / Rechazado), desacoplando la curva de consumo histórico de la exigibilidad de cobro.
9.  **Módulo 9: Reportes Administrativos, de Consumo, Deuda y Recaudación (Sección 10.1 a 10.7):**
    *   *Propósito:* Generar análisis de deudores por antigüedad, recaudación diaria/mensual, consumos por zona, avance de migración y estados de cuenta consolidados, con capacidad de exportación a Excel, CSV y PDF.
10. **Módulo 10: Portal Individual de Socios (Sección 11):**
    *   *Propósito:* Ofrecer a los socios una vista de autoservicio exclusiva y restringida a sus propios medidores, lecturas, consumos, obligaciones pendientes, historial de pagos y descarga de recibos en formato digital.
11. **Módulo 11: Seguridad, Auditoría, Copias de Seguridad y Recuperación (Sección 12.3, 14):**
    *   *Propósito:* Registrar bitácoras inalterables de auditoría de cada acción sensible, gestionar copias de seguridad automáticas y verificar periódicamente la integridad de restauración.
12. **Módulo 12: Pruebas de Aceptación, Capacitación y Puesta en Marcha (Sección 15, 16):**
    *   *Propósito:* Ejecutar las suites de validación financiera y de carga, capacitar al personal en sus respectivos roles y certificar formalmente la salida a producción.

---

## B.5. Exclusiones y Límites Explícitos (Fuera del Alcance del MVP)

Para preservar el foco del proyecto, minimizar riesgos operativos y evitar la complejidad accidental, quedan taxativamente **EXCLUIDAS del Producto Mínimo Viable (MVP)** las siguientes capacidades, las cuales quedan catalogadas como opciones futuras sujetas a aprobación formal:

*   **X-01. Contabilidad de Partida Doble Integrada:** El sistema gestionará caja y cuentas por cobrar operativas; no implementará un plan de cuentas contable general, balances de sumas y saldos ni asientos de diario.
*   **X-02. Pasarelas de Pago en Línea Bancarias / Webhooks:** No se contemplan cobros con tarjeta de crédito/débito ni débitos automáticos en el MVP. Las recaudaciones se realizarán en caja física en efectivo (o mediante verificación manual de transferencias bancarias / QR simple si el Directorio lo autoriza).
*   **X-03. Integración Tributaria Fiscal en Línea (SIAT/SIN):** No se emitirán facturas electrónicas computarizadas en línea con Código de Autorización de Emisión (CAED) hasta que la entidad no acredite formalmente su obligación tributaria.
*   **X-04. Convenios y Planes de Pago Fraccionados:** No se soportará la refinanciación de deudas en cuotas de capital con interés. Las deudas deben cancelarse en su totalidad obligación por obligación.
*   **X-05. Notificaciones Masivas Automatizadas (SMS / WhatsApp Business API / Mailgun):** La emisión de recordatorios se realizará a través del portal y reportes impresos.
*   **X-06. Aplicaciones Móviles Nativas (iOS / Android):** La accesibilidad móvil se resolverá mediante diseño web adaptable (Responsive Web Design / Progressive Web App).
*   **X-07. Telemetría y Sensores IoT:** El sistema no integrará medidores ultrasónicos inteligentes con reporte LoRaWAN o GSM. Toda lectura será introducida por operadores humanos.
*   **X-08. Gestión Integral de Inventario de Almacén:** No se controlará el stock de accesorios de fontanería, tuberías ni químicos de cloración.
*   **X-09. Modelado Hidráulico de Infraestructura Física:** No se incluirá SIG para trazado topológico de tuberías, curvas de presión ni balance de masas en tanques de almacenamiento.

---

## B.6. Actores del Sistema y Matriz de Roles

La autorización se basa en el principio de menor privilegio (Principle of Least Privilege). Se definen inicialmente los siguientes perfiles canónicos:

| Rol Canónico | Responsabilidades y Privilegios Principales | Restricciones Mandatarias |
| :--- | :--- | :--- |
| **Administrador General** | Parametrización institucional, gestión de usuarios, roles, menús, auditoría global y aprobación de tarifas. | No debe realizar cobros en caja de forma habitual para preservar la separación de funciones. |
| **Responsable Administrativo** | Gestión de socios, zonas, asignación de medidores, supervisión de padrón y aprobación de excepciones. | No puede alterar registros de auditoría ni modificar tarifas sin autorización de Directorio. |
| **Encargado de Lecturas** | Consulta de proformas, captura de lecturas mensuales y reporte de observaciones en campo. | Prohibido el acceso al módulo de cobranzas en caja y a la anulación de lecturas definitivas. |
| **Cajero** | Búsqueda de socios, cobro total de obligaciones seleccionadas, emisión de recibos y arqueo de turno de caja. | Prohibido aplicar descuentos manuales, alterar tarifas o condonar deudas unilateralmente. |
| **Responsable de Transcripción** | Digitalización de datos históricos y asignación de respaldos documentales. | Sus registros ingresan en estado `Transcrito` y no generan deuda hasta la validación de un supervisor. |
| **Supervisor de Migración** | Revisión de inconsistencias históricas, validación de transcripciones y propuesta de regularizaciones. | Requiere respaldo documental físico o digital obligatorio para validar cualquier registro observado. |
| **Socio** | Consulta exclusiva de sus propios datos, medidores, consumos, deudas y recibos digitales. | Aislamiento horizontal estricto: bajo ninguna circunstancia puede ver datos de otros socios. |
| **Auditor / Fiscalizador** | Consulta de bitácoras, reportes consolidados y trazabilidad de operaciones sin privilegios de edición. | Perfil estrictamente de solo lectura (*read-only*) sobre todos los módulos. |

---

## B.7. Los Quince Principios Constitucionales Obligatorios

Los siguientes quince (15) principios, identificados mediante códigos estables **P1** a **P15**, constituyen las leyes fundamentales del sistema:

### P1. Fidelidad de Negocio
Ninguna regla financiera, tarifaria, de membresía o de cobranza podrá modificarse, suprimirse o relajarse sin una aprobación formal y documentada del Directorio o Asamblea. Los desarrolladores y arquitectos no tienen potestad para introducir "correcciones lógicas" no autorizadas a las fórmulas de la organización.

### P2. Fuente Única de Verdad
Todos los saldos, consumos calculados, estados de cuenta, indicadores de dashboard y reportes administrativos deben derivarse de forma determinística a partir de los datos atómicos y transaccionales del sistema. Queda prohibido el almacenamiento de saldos redundantes o no reconciliables.

### P3. Integridad Financiera
Toda operación que involucre cobro de dinero, extinción de obligaciones, emisión de recibos y actualización de deudas debe ejecutarse dentro de una transacción atómica e indivisible (ACID). Si cualquier fase falla, la operación entera debe revertirse inmediatamente (*rollback* total).

### P4. Idempotencia
La repetición intencional o accidental de una operación (como reintentos por caída de red o dobles clics en la interfaz) no generará lecturas, obligaciones, membresías, cobros ni recibos duplicados. Toda solicitud sensible debe incorporar un identificador de idempotencia.

### P5. Conservación Histórica
Ningún registro que forme parte del historial operativo o financiero podrá eliminarse físicamente de la base de datos (*prohibición absoluta de DELETE en tablas transaccionales*). Las bajas, correcciones y anulaciones se gestionarán mediante estados lógicos y transacciones compensatorias que preserven la trazabilidad.

### P6. Auditoría Verificable
Toda acción relevante (altas, modificaciones, anulaciones, validaciones, inicios de sesión y exportaciones) debe registrar de forma automática e inalterable: identificador del usuario responsable, dirección IP, fecha y hora en UTC, entidad afectada, valor previo, valor modificado y justificación obligatoria en operaciones sensibles.

### P7. Seguridad por Defecto
El sistema aplicará privilegio mínimo, validación estricta de autorizaciones del lado del servidor (*server-side enforcement*), sanitización de entradas, parametrización total de consultas SQL y algoritmos criptográficos robustos para contraseñas. Ocultar componentes en la interfaz no constituye seguridad.

### P8. Transparencia Financiera
El sistema mantendrá una distinción contable y visual estricta e inconfundible entre: importe calculado teóricamente, importe histórico documentado en papeles físicos, importe facturado, importe efectivamente cobrado, saldo pendiente y conceptos anulados. Jamás se presentarán como iguales cifras que provengan de fuentes distintas.

### P9. Configuración Controlada
Las tarifas, fechas de vencimiento, parámetros institucionales y catálogos de servicios deben administrarse mediante interfaces autorizadas y persistirse con historial de vigencia. No se requerirá modificar código fuente ni reiniciar servicios para aplicar cambios tarifarios aprobados.

### P10. Validación Previa
Ninguna lectura clasificada como observada ni ninguna deuda histórica carente de respaldo documental comprobable generará automáticamente una obligación cobrable en la cuenta del socio. Todo registro dudoso permanecerá congelado hasta su validación explícita.

### P11. Continuidad Operativa
La generación periódica de copias de seguridad automatizadas, la exportación de datos a formatos estándar abiertos (CSV, JSON, SQL) y los protocolos verificados de restauración ante desastres forman parte indisoluble de los entregables del producto.

### P12. Usabilidad y Diseño Human-Centered
Los flujos de trabajo deben ser simples, intuitivos y adaptables a pantallas de computadoras de escritorio, tabletas y teléfonos móviles, con terminología clara en español, mensajes de error constructivos y pantallas de confirmación obligatoria previas a la ejecución de operaciones financieras irreversibles.

### P13. Privacidad y Aislamiento de Datos
Cada socio tendrá acceso única y exclusivamente a su propia información de consumo y pagos. Los documentos personales, actas, resoluciones y números de contacto estarán protegidos contra accesos no autorizados mediante controles de seguridad perimetral y horizontal.

### P14. Separación Estricta de Responsabilidades
La arquitectura del sistema garantizará el desacoplamiento absoluto entre la capa de presentación visual, la capa de lógica de negocio y la capa de acceso y persistencia de datos, asegurando la mantenibilidad, portabilidad y testabilidad independiente de las reglas de cálculo.

### P15. Gobernanza Constitucional
Cualquier excepción, enmienda o desviación a los principios y reglas fijados en esta Constitución exigirá la redacción de una Solicitud de Cambio Arquitectónico (RFC), una evaluación exhaustiva de impacto y riesgos, y la aprobación formal por escrito de los custodios del proyecto.

---

## B.8. Reglas de Dominio Inviolables

### 1. Socios y Parque de Medidores
*   **R-DOM-01 (Unicidad de Identidad):** Cada socio estará identificado por un Código Único generado por el sistema y por su Número de Documento de Identidad (CI). No se permitirá registrar dos socios con el mismo CI, salvo excepción debidamente justificada y autorizada por la administración.
*   **R-DOM-02 (Multi-medición):** Un socio podrá ser titular de uno o varios medidores en una o varias zonas. La deuda exigible al socio será la suma aritmética consolidada de las obligaciones pendientes de todos sus medidores y servicios vinculados.
*   **R-DOM-03 (Exclusividad de Asignación):** Un medidor físico solo podrá estar asignado a un contrato activo a la vez. No se permite la asignación concurrente de un mismo medidor a dos cuentas activas incompatibles.
*   **R-DOM-04 (Trazabilidad de Sustitución):** La reasignación, reemplazo o baja de un medidor no borrará sus lecturas ni sus cobros históricos. Al sustituir un medidor por avería o renovación, se registrará obligatoriamente la lectura final de retiro del medidor saliente y la lectura inicial de calibración del medidor entrante.
*   **R-DOM-05 (Inmutabilidad de Estados Históricos):** El cambio de estado de un socio a `Inactivo`, `Suspendido` o `Retirado` jamás eliminará sus deudas devengadas ni sus registros de consumo anteriores.

### 2. Captura y Validación de Lecturas
*   **R-DOM-06 (Fórmula de Consumo):** Para un medidor $m$ en el periodo mensual $p$, el consumo volumétrico se calcula estrictamente como:
    $$\\text{Consumo}(m, p) = \\text{Lectura Actual}(m, p) - \\text{Lectura Anterior Válida}(m, p-1)$$
*   **R-DOM-07 (Consistencia Monótona de Lectura):** El sistema bloqueará de forma nativa el registro de una lectura actual inferior a la anterior ($\text{Lectura Actual} < \text{Lectura Anterior}$), disparando un estado de `Lectura Observada`, salvo que se tramite mediante el flujo especial de reinicio de contador (*rollover*) o sustitución física del medidor.
*   **R-DOM-08 (Unicidad de Lectura Definitiva):** No se admitirán dos lecturas definitivas para el mismo medidor y periodo de facturación. Cualquier rectificación requerirá una solicitud de corrección autorizada que mantenga la versión original en auditoría.
*   **R-DOM-09 (Proforma Informativa):** La proforma de lectura mensual entregada o mostrada al socio es un comprobante de notificación de medición que no confiere acreditación de pago ni sustituye al recibo oficial.

### 3. Vigencia y Aplicación Tarifaria
*   **R-DOM-10 (No Retroactividad):** Toda modificación a los importes o límites de tramos en el tarifario entrará en vigencia exclusivamente para las obligaciones que se emitan con posterioridad a su fecha de inicio de vigencia. Las obligaciones ya generadas o pagadas retendrán permanentemente la versión de la tarifa con la que fueron liquidadas.
*   **R-DOM-11 (Detalle de Liquidación):** Cada obligación generada almacenará una copia histórica (*snapshot*) del consumo medido, la tarifa aplicada, los cargos por tramo y el desglose de conceptos adicionales.

### 4. Ciclo de Vida de Obligaciones y Membresías
*   **R-DOM-12 (Unicidad Mensual de Consumo):** Es matemáticamente imposible generar más de una obligación de consumo de agua para el mismo medidor, servicio y periodo mensual. El motor de facturación debe ser estrictamente idempotente.
*   **R-DOM-13 (Independencia de la Membresía):** La obligación de membresía/afiliación es un concepto único, no recurrente e independiente del consumo mensual de agua potable. Se genera al registrar un nuevo socio y jamás volverá a emitirse de manera automática en los periodos mensuales subsiguientes.
*   **R-DOM-14 (Cálculo de Vencimiento):** La fecha de vencimiento se computará aplicando el día fijo configurado por la institución (ej. día 15). Si en un mes determinado dicho día no existe (ej. 30 o 31 en febrero), se fijará de forma determinística el último día natural de dicho mes.

### 5. Cobranzas, Caja y Recibos
*   **R-DOM-15 (Prohibición Absoluta de Pagos Parciales):** No se aceptarán abonos parciales sobre el importe de una obligación individual. Para extinguir una obligación, el monto pagado debe ser exactamente igual al total adeudado de dicha obligación.
*   **R-DOM-16 (Liquidación Atómica Multiconcepto):** Si un socio acumula múltiples obligaciones pendientes, el cajero podrá seleccionar un subconjunto de ellas para su pago simultáneo. La transacción registrará la cancelación de todas las obligaciones seleccionadas y emitirá un único Recibo de Cobranza por el monto total exacto.
*   **R-DOM-17 (Inalterabilidad del Recibo y Anulación Lógica):** El recibo oficial emitido es inalterable. La anulación de un recibo requerirá autorización de un supervisor, registro de motivo fundado y ejecución de una transacción reversora que restablezca automáticamente las obligaciones asociadas a su estado `Pendiente`. Queda estrictamente prohibida la destrucción de la numeración correlativa del recibo.

### 6. Transcripción y Regularización Histórica
*   **R-DOM-18 (Principio del Doble Carril):** La captura de una lectura de periodos pasados únicamente alimenta la serie histórica de consumo. No se transformará en una obligación económica exigible hasta que cumpla con el flujo de validación, cotejo documental y autorización formal de deuda.
*   **R-DOM-19 (Trazabilidad de Origen):** Todo registro de transcripción registrará de forma obligatoria el operador que digitalizó los datos, la fecha de ingreso, el supervisor que validó la veracidad del dato y la referencia física o digital del documento de respaldo (número de planilla, libro de actas o cuaderno).

---

## B.9. Arquitectura y Directrices Técnicas

1.  **Patrón Arquitectónico Base:** La solución adoptará el patrón **Modelo-Vista-Controlador (MVC)** o una variante moderna de capas desacopladas (**Arquitectura Limpia / Hexagonal**), garantizando que las reglas de negocio financieras (cálculo de consumo, aplicación de tarifas y cobranza) residan en servicios de dominio puros, totalmente independientes de los controladores web y de las interfaces de usuario.
2.  **Motor de Base de Datos:** Se empleará un Sistema de Gestión de Bases de Datos Relacional (RDBMS) de clase empresarial con cumplimiento integral de **ACID** (Atomicidad, Consistencia, Aislamiento y Durabilidad), soporte nativo para restricciones de integridad referencial (`FOREIGN KEY`), índices únicos (`UNIQUE`), bloqueos transaccionales pesimistas (`SELECT ... FOR UPDATE` para caja) y tipos de datos de alta precisión para moneda (`DECIMAL/NUMERIC`).
3.  **Neutralidad Tecnológica Controlada:** La selección final del lenguaje de programación (ej. Python, TypeScript/Node.js, PHP, C#/.NET), el framework web y el motor de base de datos relacional (ej. PostgreSQL, MariaDB/MySQL) no será asumida arbitrariamente por esta Constitución. Deberá fundamentarse en un análisis multicriterio que pondere costo total de propiedad, disponibilidad de soporte en Bolivia, facilidad de mantenimiento e independencia de proveedores propietarios (**Decisión Pendiente D-15**).
4.  **Diseño de Interfaz:** La interfaz visual será 100% adaptable (*responsive*), diseñada bajo el principio *Mobile-First*, optimizada para operar eficientemente en conexiones de ancho de banda restringido y permitiendo la visualización clara y lectura táctil en dispositivos móviles de campo.

---

## B.10. Directrices de Seguridad, Privacidad y Control de Acceso

1.  **Gestión Criptográfica de Contraseñas:** Queda estrictamente prohibido el almacenamiento de contraseñas en texto claro o con funciones hash obsoletas (MD5, SHA1). Se exigirá el empleo de algoritmos con funciones de derivación de claves resistentes a ataques por fuerza bruta y GPU: **Argon2id** (preferente) o **bcrypt** (factor de costo mínimo 12).
2.  **Prohibición del Carnet como Contraseña Permanente:** Se rechaza de manera terminante el uso del número de Documento de Identidad (CI) como credencial permanente de acceso al portal. En caso de emplearse para el enrolamiento inicial, tendrá la condición de contraseña temporal de un solo uso, exigiendo su cambio obligatorio en el primer inicio de sesión.
3.  **Defensa en Profundidad (OWASP Top 10):**
    *   *Inyección SQL:* Queda proscrita la concatenación directa de cadenas en consultas a la base de datos. Se exigirá el uso sistemático de consultas preparadas parametrizadas o un ORM seguro.
    *   *Cross-Site Scripting (XSS):* Sanitización y escape contextual automático de todas las variables renderizadas en la interfaz.
    *   *Cross-Site Request Forgery (CSRF):* Inclusión obligatoria de tokens antifalsificación criptográficos en todos los formularios y peticiones mutantes (POST, PUT, DELETE).
4.  **Aislamiento y Privacidad de Datos:** El acceso a la información personal del socio estará restringido por directrices de privacidad equivalentes a las mejores prácticas internacionales. El portal del socio implementará verificaciones de propiedad a nivel de controlador (*Owner-based Authorization*), impidiendo que un socio pueda consultar registros de terceros manipulando identificadores en las URLs (*Insecure Direct Object References - IDOR*).

---

## B.11. Directrices de Integridad Financiera y Trazabilidad Transaccional

1.  **Transaccionalidad en Caja:** El flujo de cobro debe ejecutarse dentro de un bloque transaccional atómico:
    ```mermaid
    sequenceDiagram
        autonumber
        actor C as Cajero
        participant S as Sistema (Backend)
        participant DB as Base de Datos (Transacción ACID)
        
        C->>S: Confirmar Cobro (Obligaciones Seleccionadas, Monto Exacto)
        activate S
        S->>DB: INICIAR TRANSACCIÓN (BEGIN)
        S->>DB: Bloquear y verificar estado = 'Pendiente' (FOR UPDATE)
        alt Alguna obligación ya no está pendiente
            S-->>C: ERROR: Obligación alterada concurrentemente. Abortar.
            S->>DB: ROLLBACK
        else Todas las obligaciones válidas
            S->>DB: Actualizar Obligaciones a 'Pagada' (con ref Recibo)
            S->>DB: Insertar Registro Maestro de Pago y Detalle
            S->>DB: Generar Número Correlativo Oficial de Recibo
            S->>DB: Registrar Evento en Bitácora de Auditoría
            S->>DB: CONFIRMAR TRANSACCIÓN (COMMIT)
            S-->>C: ÉXITO: Recibo generado listo para impresión
        end
        deactivate S
    ```
2.  **Control de Turnos y Arqueo:** El sistema soportará opcionalmente la gestión de turnos de caja (Apertura con saldo inicial en efectivo, Registro continuo de cobros, Corte y Arqueo con declaración a ciegas de efectivo real, y Reporte de sobrantes/faltantes).
3.  **Prohibición de Manipulación Manual de Totales:** Los cajeros carecen de permisos para sobreescribir los importes calculados por el sistema. Cualquier descuento, exención o ajuste debe sustentarse en una regla tarifaria institucional previamente parametrizada y auditada.

---

## B.12. Directrices para Transcripción y Regularización Histórica

El módulo de transcripción histórica operará bajo un riguroso ciclo de vida de seis (6) estados para garantizar la pureza de la información:

```mermaid
stateDiagram-v2
    [*] --> Pendiente: Registro identificado en planilla/cuaderno
    Pendiente --> Transcrito: Operador digitaliza datos y lectura
    Transcrito --> Observado: Error de consistencia o falta respaldo
    Transcrito --> Validado: Supervisor verifica y aprueba contra documento físico
    Observado --> Validado: Aclaración documentada y corrección autorizada
    Observado --> Rechazado: Registro insubsanable o duplicado
    Validado --> Migrado: Incorporación formal al historial del sistema
    Migrado --> [*]
    Rechazado --> [*]
```

1.  **Inmutabilidad de la Información Validada:** Un registro en estado `Validado` o `Migrado` no podrá ser modificado de manera directa. Cualquier corrección ulterior demandará un procedimiento extraordinario de reapertura auditado.
2.  **Cálculo vs. Respaldo:** El sistema exhibirá siempre dos columnas en los reportes de migración: `Importe Calculado por Sistema` e `Importe Documentado en Fuente Original`. Si ambas magnitudes difieren, el registro pasará forzosamente a estado `Observado` hasta la ratificación formal de la diferencia.

---

## B.13. Directrices de Calidad, Pruebas y Criterios de Aceptación

Para asegurar que ninguna regresión o falla matemática alcance el entorno operativo, se instituyen las siguientes obligaciones de calidad:

1.  **Pruebas de Frontera Tarifaria:** Toda versión candidata a despliegue deberá superar suites de pruebas automatizadas que verifiquen con exactitud los puntos de frontera: $0, 9, 10, 12, 14, 15, 16 \\text{ y } 50 \\text{ m}^3$, así como consumos nulos o superiores a rangos normales.
2.  **Pruebas de Concurrencia e Idempotencia:** Se simularán intentos concurrentes de pago sobre una misma obligación y llamadas repetitivas al motor de generación mensual para certificar la inexistencia de duplicaciones.
3.  **Criterios de Aceptación Globales:** El sistema solo será aceptable para puesta en marcha cuando cumpla satisfactoriamente con los criterios de aceptación formales de la Sección 16 del documento fuente (ver Parte D).

---

## B.14. Directrices de Continuidad Operativa, Respaldo y Recuperación

1.  **Políticas de Respaldo:**
    *   *Copias Completas:* Respaldo automatizado diario de la base de datos completa y de los archivos multimedia (documentos y fotografías adjuntas).
    *   *Retención:* Almacenamiento rotativo de respaldos diarios durante 30 días, respaldos mensuales durante 12 meses y respaldos anuales permanentes.
2.  **Pruebas Verificables de Restauración:** No se considerará válido un respaldo que no haya sido sometido a pruebas periódicas de restauración (simulacro trimestral de recuperación en un entorno aislado).
3.  **Objetivos de Recuperación:**
    *   *RPO (Recovery Point Objective):* Máximo 24 horas de pérdida de datos transaccionales en caso de catástrofe mayor en el servidor local.
    *   *RTO (Recovery Time Objective):* Restauración operativa total del servicio en un tiempo inferior a 4 horas.

---

## B.15. Gobernanza SDD y Control de Cambios Constitucionales

1.  **Jerarquía Normativa del Proyecto:**
    *   **Nivel 1:** La presente Constitución SDD v1.0 (Norma Suprema).
    *   **Nivel 2:** Especificaciones Funcionales y de Arquitectura por Módulo (Specs).
    *   **Nivel 3:** Registros de Decisiones de Arquitectura (ADR).
    *   **Nivel 4:** Planes de Tareas, Código Fuente y Pruebas Unitarias/Integración.
2.  **Procedimiento de Enmienda Constitucional:** Toda propuesta de modificación a los Principios (P1 a P15), a las Reglas de Dominio o al Alcance Oficial deberá canalizarse mediante un documento formal de propuesta (*RFC - Request for Comments*), detallando justificación, análisis de riesgos y aprobación colegiada unánime de los responsables técnicos e institucionales.
"""

