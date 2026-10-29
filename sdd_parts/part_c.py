# -*- coding: utf-8 -*-
"""
PARTE C: REGISTRO FORMAL DE DECISIONES PENDIENTES (D-01 a D-20)
"""

def get_part_c():
    return """
# PARTE C. REGISTRO FORMAL DE DECISIONES PENDIENTES

El presente registro consolida las decisiones de negocio, organizativas, normativas y tecnológicas que permanecen pendientes de ratificación por parte de los órganos de gobierno de la institución (Directorio o Asamblea General). Para cada ítem se establece su origen en la fuente, las alternativas viables, su impacto y su condición de bloqueo.

---

### D-01: Estructura Tarifaria Definitiva y Resolución de la Anomalía para Consumos Superiores a 15 m³
*   **Sección Fuente:** Sección 2.1 (P20 a P48), Sección 5.3 (P266 a P281), Sección 17 (P863 a P877).
*   **Clasificación:** Decisión Pendiente [D] / Requisito Explícito en Fuente con advertencia expresa.
*   **Descripción del Problema:** La fuente define: 0-9 m³ = Bs 15; 10-15 m³ = Bs 15 + 2(c - 9); >15 m³ = Bs 20 total. Esto genera que 15 m³ cueste Bs 27 y 16 m³ cueste Bs 20. Se reconoce como "reducción deliberada según la interpretación adoptada", pero exige ratificación formal.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Conservar regla fuente):* Cobrar tarifa plana de Bs 20 para cualquier consumo superior a 15 m³. (Riesgo: derroche de agua, pérdida de ingresos, inequidad).
    *   *Alternativa 2 (Estructura incremental continua estándar AAPS):* Mantener los primeros tramos y tarifar cada m³ adicional sobre 15 con una tarifa superior (ej. Bs 2.50 o Bs 3.00 por m³ excedente). Fórmula: Si $c > 15$, $T(c) = 27 + P_3(c - 15)$.
    *   *Alternativa 3 (Cargo fijo más precio volumétrico uniforme):* Cargo base de Bs 15 (incluye 9 m³) y cobro lineal de Bs 2 por cada m³ adicional sin límite superior.
*   **Impacto:** Crítico en la recaudación, sostenibilidad del acuífero y equidad social entre socios.
*   **Responsable por Confirmar:** Asamblea General de Socios y Directorio del Comité.
*   **Recomendación Técnica No Vinculante:** Adoptar la Alternativa 2 o 3 para asegurar monotonía creciente, fomentar el uso racional del agua y evitar distorsiones económicas.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FACTURACIÓN REAL.** El módulo de cálculo de consumo no podrá activarse en producción hasta que se apruebe la tabla tarifaria definitiva.

---

### D-02: Importe Oficial, Excepciones y Tratamiento Histórico de la Membresía
*   **Sección Fuente:** Sección 2.6 (P77 a P89), Sección 5.1 (P216 a P237), Sección 6.3 (P322 a P335), Sección 17 (P863 a P877).
*   **Clasificación:** Decisión Pendiente [D] / Requisito Explícito [A] (concepto obligatorio, importe indefinido).
*   **Descripción del Problema:** Se estipula que cada socio nuevo genera automáticamente una obligación de membresía única, pero la fuente aclara que su importe no está definido. Tampoco se define el tratamiento para los socios fundadores migrados desde registros antiguos.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Fijar un importe único estándar (ej. Bs 100 o Bs 500) para todo socio nuevo, y marcar a los socios históricos migrados como "Exentos / Ya Cancelado en Gestión Previa".
    *   *Alternativa 2:* Establecer categorías de membresía (Socio Fundador = Bs 0, Socio Activo Nuevo = Monto X, Transferencia de Derecho = Monto Y).
*   **Impacto:** Directo sobre el flujo de caja inicial y la incorporación legal de los socios al padrón.
*   **Responsable por Confirmar:** Directorio del Comité / Asamblea General.
*   **Recomendación Técnica No Vinculante:** Parametrizar el importe en el Módulo 1 y habilitar una bandera (*flag*) en la migración histórica para registrar a los socios preexistentes con estado `Membresía Regularizada Históricamente` sin generarles deuda económica.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA ALTA DE SOCIOS Y PRODUCCIÓN.** Impide la creación definitiva de socios sin incurrir en deudas ficticias o inconsistencias.

---

### D-03: Fijación del Día de Vencimiento y Reglas para Días Inexistentes o Feriados
*   **Sección Fuente:** Sección 2.3 (P59 a P66), Sección 17 (P863 a P877).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** La fuente sugiere a modo de ejemplo el día 15 de cada mes y establece que para meses más cortos se aplicará el último día del mes. Falta formalizar el día oficial y qué ocurre si el vencimiento cae en fin de semana o feriado nacional en Bolivia.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Día 15 fijo del mes calendario siguiente. Si cae en domingo/feriado, vence el siguiente día hábil.
    *   *Alternativa 2:* Día fijo (ej. 20 o último día de mes) sin prórroga por feriados, dado que el portal web está operativo 24/7.
*   **Impacto:** Determina el cálculo de mora, reportes de deudores y corte de servicio (si aplica).
*   **Responsable por Confirmar:** Directorio / Administración.
*   **Recomendación Técnica No Vinculante:** Fijar el día 15 o 20 del mes subsiguiente a la lectura, con corrimiento automático al primer día hábil bancario/laboral si coincide con fin de semana o feriado.
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA ARQUITECTURA / BLOQUEANTE PARA EMISIÓN DE OBLIGACIONES.**

---

### D-04: Modalidad de Generación de Obligaciones (Automática, Programada o Confirmada)
*   **Sección Fuente:** Sección 7.5 (P431 a P443), Sección 17 (P863 a P877).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** Determinar si las obligaciones de pago mensuales deben emitirse de forma inmediata al registrar cada lectura, automáticamente mediante una tarea programada (*cron job*) el día 1 de cada mes, o previa revisión y clic de aprobación expresa por parte del Administrador.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Generación Manual por Lote Confirmada):* El Administrador revisa las lecturas del periodo y presiona "Emitir Obligaciones del Periodo".
    *   *Alternativa 2 (Generación Automática Programada):* El sistema corre un proceso en background en una fecha fija procesando únicamente las lecturas validadas.
*   **Impacto:** Control operativo versus automatización; prevención de emisiones masivas erróneas.
*   **Responsable por Confirmar:** Responsable Administrativo.
*   **Recomendación Técnica No Vinculante:** Adoptar la Alternativa 1 (Generación Confirmada por Lote) para el MVP, permitiendo al administrador inspeccionar el resumen de lecturas observadas antes de disparar las cuentas por cobrar.
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA DATOS MAESTROS / BLOQUEANTE PARA FASE 3 (CONSUMO).**

---

### D-05: Políticas de Caja, Medios de Pago, Vuelto, Prelación de Deuda y Conciliación
*   **Sección Fuente:** Sección 2.4 (P67 a P71), Sección 9.1 a 9.5 (P552 a P623), Sección 17 (P863 a P877).
*   **Clasificación:** Decisión Pendiente [D] / Requisito Explícito [A].
*   **Descripción del Problema:** La fuente impone no permitir pagos parciales sobre obligaciones individuales. Sin embargo, no define si ante varias obligaciones vencidas el socio puede elegir arbitrariamente cuál pagar (ej. mes actual saltando meses anteriores) o si debe regir la prelación cronológica (FIFO). Tampoco se detalla la operativa de control de cambio/vuelto ni soporte para QR simple.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Selección Libre):* El cajero marca cualquier obligación a solicitud del socio. (Riesgo: acumulación de deuda antigua y prescripción de cobro).
    *   *Alternativa 2 (Prelación Estricta FIFO):* El sistema exige pagar primero la obligación más antigua pendiente antes de permitir la selección de periodos recientes.
*   **Impacto:** Legalidad tributaria, prevención de prescripción de deudas y cuadratura física de dinero en caja.
*   **Responsable por Confirmar:** Directorio y Cajero Principal.
*   **Recomendación Técnica No Vinculante:** Imponer por defecto la regla FIFO para evitar prescripción de cobros, y dotar a la pantalla de cobro de una calculadora de "Efectivo Recibido" y "Cambio/Vuelto a Entregar".
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FASE 4 (CAJA).**

---

### D-06: Política de Descuentos, Exenciones, Multas por Mora y Anulación de Recibos
*   **Sección Fuente:** Sección 2.6 (P86), Sección 9.2 (P574), Sección 9.4 (P609), Sección 17 (P868).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** El documento prohíbe reducir importes manualmente en caja, señalando que los ajustes o exenciones solo operarán bajo "reglas autorizadas". Se requiere definir formalmente si existen descuentos (ej. Ley del Adulto Mayor en Bolivia, 20% sobre agua potable en tarifa básica) y cuáles son los motivos válidos y plazos máximos para anular un recibo.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Sin descuentos ni multas en el MVP. Anulaciones permitidas exclusivamente durante el mismo turno de caja con autorización de supervisor.
    *   *Alternativa 2:* Parametrizar tipos de descuento autorizados (ej. Tercera Edad, Sede Social comunitaria) y permitir anulación justificada con reversión automática dentro de las 24 horas.
*   **Impacto:** Cumplimiento de normativas sociales bolivianas e integridad de los fondos auditados.
*   **Responsable por Confirmar:** Directorio del Comité / Asesor Legal.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 2, limitando la anulación de recibos al mismo día de emisión y exigiendo la presencia física del recibo original devuelto.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA OPERACIÓN DE CAJA.**

---

### D-07: Procedimiento para Lecturas Faltantes, Estimaciones, Averías y Reinicios de Medidor
*   **Sección Fuente:** Sección 2.2 (P57), Sección 5.2 (P261), Sección 7.3 (P403 a P413), Sección 17 (P869).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** ¿Qué se factura cuando un medidor es inaccesible (predio cerrado, medidor destruido o empañado)? ¿Cómo se procesa un reinicio de contador cuando el medidor sobrepasa los 9999 m³ y vuelve a 0000 m³ (*rollover*)?
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Facturar la tarifa básica mínima (9 m³ = Bs 15) como cuota fija presuntiva.
    *   *Alternativa 2 (Cálculo promedio histórico):* Promedio de los últimos 3 periodos válidos, con regularización en la siguiente lectura real (estándar AAPS).
    *   *Alternativa 3 (Para rollover):* Fórmula adaptada: $\\text{Consumo} = (10000 - \\text{Lectura Anterior}) + \\text{Lectura Actual}$.
*   **Impacto:** Continuidad del ingreso mensual sin generar quejas por sobrefacturación.
*   **Responsable por Confirmar:** Responsable de Lecturas y Directorio.
*   **Recomendación Técnica No Vinculante:** Adoptar la Alternativa 2 para medidores no leídos y la Alternativa 3 para reinicios de cuadrante mediante una bandera de regularización explícita.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FASE 3 (CONSUMO).**

---

### D-08: Naturaleza Tributaria y Legal del Recibo (Recibo Interno vs. Factura SIAT)
*   **Sección Fuente:** Sección 3.2 (P142), Sección 9.4 (P597 a P613), Sección 17 (P870).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** Determinar si la organización cuenta con Número de Identificación Tributaria (NIT) activo ante el Servicio de Impuestos Nacionales (SIN) y si está categorizada en el Régimen General obligada a facturación electrónica SIAT, o si opera legalmente como CAPYS/Cooperativa exenta con Recibo Oficial Interno de Cobranza.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Recibo Oficial Interno Comunitario):* Documento no fiscal autorizado por estatutos de la asociación/AAPS con numeración correlativa interna.
    *   *Alternativa 2 (Factura Electrónica SIAT Modalidad Computarizada en Línea):* Integración con servicios SOAP/REST del SIN, firma digital, código CUF/CUFD y QR fiscal.
*   **Impacto:** Complejidad arquitectónica mayúscula, costos de certificados y dependencia externa.
*   **Responsable por Confirmar:** Directorio Institucional y Asesor Contable/Tributario.
*   **Recomendación Técnica No Vinculante:** Implementar en el MVP la Alternativa 1 (Recibo Interno Comunitario). Diseñar la tabla de pagos con desacoplamiento suficiente para conectar un servicio SIAT en Fase 2 si fuera formalmente exigido.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FORMATO DEFINITIVO DE RECIBO.**

---

### D-09: Periodos Históricos a Migrar, Documentos Aceptables y Nivel de Supervisión
*   **Sección Fuente:** Sección 8.1 a 8.7 (P444 a P548), Sección 17 (P871).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** Definir con precisión el límite temporal de la migración (ej. últimos 12 meses, últimos 5 años o desde la fundación), los documentos válidos (cuadernos manuscritos, hojas sueltas, planillas Excel) y quiénes tendrán el rol de validación de los datos.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Migración Integral Total):* Transcribir todo el archivo histórico existente sin importar su antigüedad. (Riesgo de dilatación del proyecto y datos ilegibles).
    *   *Alternativa 2 (Migración Escalonada Priorizada):* Migrar inicialmente los últimos 12 meses para calibrar curvas de consumo y las deudas vigentes respaldadas en actas firmadas.
*   **Impacto:** Costos operativos de digitalización, tiempo de salida a producción y carga en base de datos.
*   **Responsable por Confirmar:** Comisión de Transcripción y Directorio.
*   **Recomendación Técnica No Vinculante:** Adoptar la Alternativa 2 (últimos 12 a 24 meses como horizonte operativo).
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FASE 5 (MIGRACIÓN HISTÓRICA).**

---

### D-10: Política de Incorporación de Deudas Históricas al Estado de Cuenta Actual
*   **Sección Fuente:** Sección 8.7 (P536 a P548), Sección 17 (P872).
*   **Clasificación:** Decisión Pendiente [D] / Regla Crítica de Fuente.
*   **Descripción del Problema:** La fuente exige que transcribir una lectura histórica no genere automáticamente una deuda cobrable. Falta reglamentar el mecanismo institucional por el cual una deuda antigua transcrita se convierte formalmente en una obligación exigible en caja.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Exigir la firma de un acta de conciliación individual entre el socio y la administración antes de activar la deuda en el sistema.
    *   *Alternativa 2:* Aprobación por resolución de Directorio de una nómina oficial de saldos deudores históricos al corte de migración.
*   **Impacto:** Paz social en la comunidad, legitimidad de cobro y riesgo de controversias legales.
*   **Responsable por Confirmar:** Directorio y Asamblea General de Socios.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 2 mediante un proceso batch en el sistema denominado "Consolidación y Activación de Cartera Histórica Aprobada".
*   **Condición de Bloqueo:** **BLOQUEANTE PARA COBRO DE DEUDAS PASADAS.**

---

### D-11: Modelo de Relación Estructural (Socio - Inmueble - Contrato - Medidor)
*   **Sección Fuente:** Sección 1 (P3), Sección 2.5 (P72 a P76), Sección 5.2 (P238 a P265), Sección 6.1 a 6.7.
*   **Clasificación:** Decisión Pendiente [D] / Principio Derivado [B].
*   **Descripción del Problema:** Resolver definitivamente si la relación del medidor es directa con el socio o a través de un inmueble/contrato de suministro.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Modelo Simplificado):* Socio $\\leftrightarrow$ Medidor (relación directa 1 a N). (No modela predios ni inquilinos; dificulta traspasos).
    *   *Alternativa 2 (Modelo Integral de Servicios Públicos):* Socio (Titular de Derecho) $\\rightarrow$ Predio/Inmueble (Ubicación física en Zona) $\\rightarrow$ Contrato/Cuenta de Servicio $\\rightarrow$ Medidor (Activo físico con historial de lectura).
*   **Impacto:** Arquitectura de base de datos, normalización de esquemas e integridad ante compraventa de inmuebles.
*   **Responsable por Confirmar:** Arquitecto de Software y Administrador del Comité.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 2 (Modelo Integral), simplificando la interfaz de usuario para que el operador solo perciba el flujo Socio-Medidor en casos cotidianos.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA DISEÑO DE BASE DE DATOS (FASE 2).**

---

### D-12: Modelo de Despliegue y Tenencia (Instalación Independiente vs. Plataforma Multi-Tenant)
*   **Sección Fuente:** Sección 1 (P1 a P5), Sección 3.2 (P136 a P148), Sección 14 (P785 a P799).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** ¿El software se implementará como una instancia aislada para un único comité de agua (*Single-Tenant* on-premise o VPS propio), o se diseñará como una plataforma SaaS multi-asociación (*Multi-Tenant*) donde varias cooperativas compartan infraestructura con aislamiento lógico de esquemas?
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Single-Tenant):* Una base de datos y un servidor independiente por organización. (Máxima simplicidad, soberanía total de datos para la cooperativa, nulo riesgo de fuga interinstitucional).
    *   *Alternativa 2 (Multi-Tenant SaaS):* Una sola aplicación centralizada con discriminación por `organization_id` o esquemas PostgreSQL separados. (Menor costo de mantenimiento centralizado, pero mayor complejidad de seguridad).
*   **Impacto:** Costos de infraestructura, modelo de negocio y gobernanza de la base de datos.
*   **Responsable por Confirmar:** Equipo Directivo y Patrocinadores del Proyecto.
*   **Recomendación Técnica No Vinculante:** Diseñar la arquitectura con soporte modular para la Alternativa 1 (Single-Tenant) en el MVP, manteniendo la clave de organización abstraída para facilitar una eventual transición a Multi-Tenant si se decide comercializar la plataforma.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA ARQUITECTURA DE DATOS Y ENTORNO DE DESPLIEGUE.**

---

### D-13: Activación, Recuperación y Seguridad de Cuentas en el Portal del Socio
*   **Sección Fuente:** Sección 11 (P724 a P739), Sección 12.1 a 12.3 (P741 a P770).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** ¿Cómo se entregan las credenciales iniciales a los socios comunitarios (muchos de ellos adultos mayores o sin correo electrónico)? ¿Cómo se gestiona el restablecimiento de contraseñas olvidadas?
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Enrolamiento Presencial en Ventanilla):* El cajero o administrador imprime una tarjeta/talón de activación con un usuario generado (`mlopez` o código de socio) y una contraseña temporal aleatoria de un solo uso.
    *   *Alternativa 2 (Autoservicio Digital con OTP):* Envío de enlaces de activación por correo electrónico o código OTP por SMS/WhatsApp. (Costoso y poco realista en comunidades rurales donde no todos tienen smartphone o saldo).
*   **Impacto:** Tasa de adopción del portal, carga de trabajo administrativo y seguridad informática.
*   **Responsable por Confirmar:** Responsable Administrativo y Soporte Técnico.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 1 para el MVP (talón impreso de enrolamiento con forzado de cambio de clave en primer acceso), complementada con restablecimiento administrativo presencial.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FASE 6 (PORTAL DEL SOCIO).**

---

### D-14: Gestión Operativa de Caja (Turnos y Arqueos Obligatorios vs. Registro Continuo)
*   **Sección Fuente:** Sección 9.5 (P614 a P623), Sección 10.5 (P687 a P698).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** La fuente menciona la apertura, cierre y arqueo de caja con una cláusula condicional: *“si la organización adopta ese procedimiento”*. Se debe ratificar si el módulo de caja debe exigir turnos de caja estrictos o si permitirá cobros continuos fechados sin apertura formal.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Turnos Estrictos de Caja):* Ningún cobro puede ejecutarse sin un turno abierto con saldo inicial; al final del día se exige arqueo ciego y cierre de turno.
    *   *Alternativa 2 (Cobranza Continua Abierta):* Cobros vinculados directamente al usuario cajero y a la fecha del sistema sin ceremonia de apertura/cierre.
*   **Impacto:** Disciplina financiera en ventanilla y prevención de faltantes de caja.
*   **Responsable por Confirmar:** Directorio y Responsable Contable/Cajero.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 1 como estándar constitucional, permitiendo un modo simplificado configurable si la organización opera con un solo cajero.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA FASE 4 (CAJA).**

---

### D-15: Stack Tecnológico Definitivo, Motor de Base de Datos y Entorno de Alojamiento
*   **Sección Fuente:** Sección 14 (P785 a P799), Sección 17 (P877).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** La fuente señala explícitamente: *“La selección definitiva de lenguaje, framework, base de datos y servidor deberá realizarse antes de iniciar el desarrollo, dejando documentado el entorno de instalación.”* Se deben evaluar opciones según costo, soporte y confiabilidad.
*   **Alternativas Evaluadas:**
    *   *Stack A (Python / Django / PostgreSQL):* Máxima robustez, transacciones ACID nativas, ORM maduro, excelente panel de auditoría, amplio soporte de desarrolladores en Bolivia.
    *   *Stack B (Node.js / TypeScript / NestJS o Express / PostgreSQL):* Arquitectura reactiva moderna, ecosistema unificado de tipado, alta concurrencia.
    *   *Stack C (PHP / Laravel / MySQL o MariaDB):* Despliegue sumamente económico en hostings compartidos locales o VPS de bajo costo, curva de mantenimiento accesible.
*   **Impacto:** Costos operativos recurrentes, curva de aprendizaje, portabilidad y ciclo de vida del software.
*   **Responsable por Confirmar:** Arquitecto de Software y Custodio Tecnológico Institucional.
*   **Recomendación Técnica No Vinculante:** Seleccionar PostgreSQL como motor innegociable de base de datos debido a su robustez transaccional y cumplimiento estricto de ACID. Para backend, recomendar Django o Laravel por su estabilidad y herramientas nativas de administración y seguridad.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA EL INICIO DE FASE 1 DE IMPLEMENTACIÓN.**

---

### D-16: Métodos de Captura de Lecturas en Campo (Planilla Física, Captura Móvil PWA y Foto)
*   **Sección Fuente:** Sección 7.1 a 7.4 (P374 a P430), Sección 14 (P785 a P799).
*   **Clasificación:** Decisión Pendiente [D] / Mejora Propuesta [C].
*   **Descripción del Problema:** ¿Cómo relevará las lecturas el encargado en campo? ¿Se mantendrá la impresión de una proforma/planilla física para posterior transcripción en oficina, o se dotará al operador de una vista móvil responsiva (PWA) con almacenamiento local temporal y captura fotográfica del cuadrante del medidor?
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Tradicional):* Impresión de planilla de toma de lecturas, llenado en papel con bolígrafo y tipeo posterior en oficina. (Lento, propenso a doble error de transcripción).
    *   *Alternativa 2 (Digital Responsiva Móvil en Campo):* Ingreso directo en teléfono o tableta con validación en línea y almacenamiento opcional de fotografía como respaldo de prueba ante reclamos del socio.
*   **Impacto:** Eficiencia operativa, reducción del ciclo mensual de facturación y respaldo objetivo ante controversias por lecturas anómalas.
*   **Responsable por Confirmar:** Responsable de Lecturas y Directorio.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 2 como interfaz web responsive (PWA) manteniendo la capacidad de imprimir planillas físicas de contingencia (**Alternativa 1**).
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA BACKEND / BLOQUEANTE PARA INTERFAZ DE LECTURAS.**

---

### D-17: Catálogo de Servicios Adicionales Autorizados y Modalidades de Cobro
*   **Sección Fuente:** Sección 5.1 (P216 a P237).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** La fuente menciona servicios adicionales como "Recojo de basura" y "Otros servicios autorizados", distinguiendo cuotas fijas periódicas, pagos únicos y cobros eventuales. Falta ratificar la nómina oficial de servicios que la entidad está facultada para recaudar.
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Limitar el MVP estrictamente a: Agua Potable (consumo por lecturas), Membresía (pago único) y Cuota de Mantenimiento de Red (cuota fija mensual).
    *   *Alternativa 2:* Incorporar módulos de cobro para servicios tercerizados o comunales (Aseo Urbano, Multa por Inasistencia a Asambleas, Reconexión de Medidor).
*   **Impacto:** Diversificación de la recaudación versus complejidad en los reportes de cobranza.
*   **Responsable por Confirmar:** Directorio del Comité.
*   **Recomendación Técnica No Vinculante:** Habilitar un catálogo flexible y parametrizable en base de datos que soporte cobros fijos y eventuales, activando inicialmente en el MVP solo Agua, Membresía y Derecho de Reconexión.
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA MVP DE AGUA.**

---

### D-18: Precisión de Lecturas, Decimales de Medidor y Reglas de Redondeo Monetario
*   **Sección Fuente:** Sección 2.1 (P20 a P48), Sección 2.2 (P49 a P58).
*   **Clasificación:** Decisión Pendiente [D] / Principio Derivado [B].
*   **Descripción del Problema:** ¿Los medidores de la organización se leen truncando a metros cúbicos enteros o se registran fracciones decimales (litros / cuadrantes rojos)? En los cobros en efectivo en ventanilla en Bolivia, donde la moneda fraccionaria menor a 10 o 50 centavos es de escasa circulación, ¿cómo se redondea el importe final?
*   **Alternativas Evaluadas:**
    *   *Alternativa 1 (Enteros de Consumo y Moneda Exacta):* Lecturas en enteros de m³ (piso/truncamiento). Facturación con dos decimales exactos (`DECIMAL(12,2)`). Redondeo matemático bancario (half-to-even) en caso de fracciones.
    *   *Alternativa 2 (Redondeo de Caja al Entero o 0.50 Bs):* Ajuste por redondeo en caja con cuenta de compensación específica.
*   **Impacto:** Cuadratura contable, discrepancias de centavos en ventanilla y facilidad en la toma de lectura en campo.
*   **Responsable por Confirmar:** Directorio y Responsable de Lecturas.
*   **Recomendación Técnica No Vinculante:** Medición en metros cúbicos enteros ($m^3$) sin decimales (estándar en comités de agua bolivianos). Cálculo financiero exacto en bolivianos con dos decimales.
*   **Condición de Bloqueo:** **BLOQUEANTE PARA MOTOR DE CONSUMO Y CAJA.**

---

### D-19: Políticas de Retención, Protección de Datos Personales y Exportación Segura
*   **Sección Fuente:** Sección 3.3, Sección 6.7, Sección 11, Sección 12.3, Sección 14.
*   **Clasificación:** Decisión Pendiente [D] / Requisito Explícito [A].
*   **Descripción del Problema:** La fuente prohíbe la eliminación física de socios, medidores y registros históricos. Se debe reglamentar el tiempo de conservación de respaldos en caliente y en frío, y las restricciones legales para la exportación de padrones de socios en formatos abiertos (prevención de fuga de bases de datos para fines políticos o comerciales ajenos al servicio).
*   **Alternativas Evaluadas:**
    *   *Alternativa 1:* Exportación libre en Excel/PDF para cualquier usuario con rol administrativo.
    *   *Alternativa 2:* Exportación condicionada a privilegio especial explícito, con inserción de marca de agua digital con el usuario que exportó y registro obligatorio de evento en la bitácora de auditoría.
*   **Impacto:** Seguridad institucional, privacidad societaria y cumplimiento de garantías constitucionales de privacidad.
*   **Responsable por Confirmar:** Directorio y Asesor Legal.
*   **Recomendación Técnica No Vinculante:** Implementar la Alternativa 2 para resguardar el padrón comunitario de socios.
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA MODELO / BLOQUEANTE PARA EXPORTACIÓN.**

---

### D-20: Dimensionamiento Inicial del Padrón, Concurrencia Esperada y Parámetros de Rendimiento
*   **Sección Fuente:** Sección 1 (P1 a P5), Sección 14 (P785 a P799).
*   **Clasificación:** Decisión Pendiente [D].
*   **Descripción del Problema:** Falta cuantificar el tamaño de la organización objetivo: número estimado de socios activos (ej. 300 socios en una pequeña comunidad vs. 5,000 en un distrito periurbano), cantidad de medidores, puestos de cobro en caja simultáneos y tasa de concurrencia esperada en el portal durante los días de vencimiento.
*   **Alternativas Evaluadas:**
    *   *Escenario Rural/Comunitario Pequeño:* 200 a 800 socios, 1 estación de caja, 1 lector de medidores, servidor local básico o VPS mínimo (1 vCPU, 2 GB RAM).
    *   *Escenario Urbano/Periurbano Mediano:* 1,000 a 10,000 socios, 3 a 5 cajeros concurrentes, múltiples lectores, servidor en nube (2-4 vCPU, 8 GB RAM, almacenamiento SSD y balanceador).
*   **Impacto:** Dimensionamiento de hardware, costos de alojamiento y afinamiento de índices de base de datos.
*   **Responsable por Confirmar:** Directorio Institucional.
*   **Recomendación Técnica No Vinculante:** Diseñar el sistema optimizado para una escala base de hasta 5,000 socios y 7,000 medidores con tiempos de respuesta en consultas de caja inferiores a 200 milisegundos.
*   **Condición de Bloqueo:** **NO BLOQUEANTE PARA DESARROLLO / BLOQUEANTE PARA APROVISIONAMIENTO DE PRODUCCIÓN.**
"""

