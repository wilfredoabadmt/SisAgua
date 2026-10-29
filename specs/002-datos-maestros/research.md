# Investigación Técnica y Decisiones de Arquitectura: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 0 — Investigación y Decisiones Técnicas  
> **Fecha:** Octubre 2026  

---

## 1. Decisiones de Arquitectura y Diseño

### DEC-008: Modularización de Apps en Django para Fase 2
- **Contexto:** Fase 2 abarca entidades fundamentales de la comunidad: Zonas territoriales, Socios, Servicios y Tarifas, y Medidores físicos.
- **Alternativas consideradas:**
  1. *Monolito en una sola app `apps/maestros`:* Concentra todo en un solo módulo, pero viola la separación de responsabilidades y complica los límites de dominio para las Fases 3 (Consumo) y 4 (Caja).
  2. *Modularización limpia por dominios funcionales:*
     - `apps/socios`: Administra `Zona` y `Socio`.
     - `apps/servicios`: Administra `Servicio`, `Tarifario`, `TramoTarifario` y la entidad transversal `Obligacion` (cuentas por cobrar devengadas).
     - `apps/medidores`: Administra `Medidor` y `AsignacionMedidor`.
- **Decisión:** **Alternativa 2 (Modularización limpia por dominios).** Permite que la app `servicios` gobierne tanto los conceptos de cobro como las obligaciones resultantes, mientras que `medidores` maneja el ciclo de vida del hardware de medición y `socios` la personería jurídica/natural de los afiliados.

---

### DEC-009: Alta Atómica de Socio y Membresía Única (R-DOM-13)
- **Contexto:** El requisito funcional explícito (Sección 6.3 de la fuente y R-DOM-13) exige que al registrar un nuevo socio, el sistema genere automáticamente e indivisiblemente una obligación de membresía única por el monto configurado. No debe permitirse crear el socio si la membresía falla, ni debe crearse más de una membresía para el mismo socio.
- **Implementación Técnica:**
  - El servicio `registrar_socio()` en `apps.socios.services` ejecuta un bloque `transaction.atomic()`.
  - Crea el registro del socio en la base de datos.
  - Consulta el servicio activo configurado con modalidad `PAGO_UNICO_MEMBRESIA` o el monto por defecto de membresía institucional.
  - Verifica mediante `Obligacion.objects.filter(socio=socio, servicio__modalidad_cobro='PAGO_UNICO_MEMBRESIA').exists()` que no exista una obligación previa.
  - Crea la `Obligacion` con estado `PENDIENTE`, fecha de emisión actual y vencimiento según la regla institucional R-DOM-14.
  - Si ocurre cualquier error, se ejecuta un *rollback* completo de la transacción y se levanta una excepción de negocio.
  - Se registra la creación en `BitacoraAuditoria` con los detalles del socio y la obligación generada.

---

### DEC-010: Exclusividad de Asignación y Ciclo de Vida del Medidor (R-DOM-03, R-DOM-04)
- **Contexto:** Un medidor físico solo puede estar asignado a un contrato/socio activo a la vez. No se permite asignación concurrente. Además, se debe conservar el historial de asignaciones y registrar la lectura de instalación y la lectura de retiro obligatoria.
- **Implementación Técnica:**
  - Modelo `Medidor`:
    - Campos: `codigo`, `numero_serie`, `marca`, `modelo`, `diametro`, `lectura_inicial`, `estado` (`DISPONIBLE`, `INSTALADO`, `MANTENIMIENTO`, `RETIRADO`, `DE_BAJA`), `observaciones`.
  - Modelo `AsignacionMedidor`:
    - Campos: `medidor` (FK), `socio` (FK), `fecha_asignacion` (Date), `lectura_instalacion` (Decimal), `fecha_retiro` (Date, null=True), `lectura_retiro` (Decimal, null=True), `motivo_retiro` (CharField, null=True), `activo` (Boolean, default=True).
    - **Restricción de Exclusividad:** En la base de datos se implementa una restricción condicional única (`UniqueConstraint` con `condition=Q(activo=True)` sobre `medidor`), garantizando a nivel de motor de base de datos que jamás existan dos asignaciones activas para el mismo medidor físico.
    - El servicio `asignar_medidor()` valida que el medidor esté en estado `DISPONIBLE`, crea la asignación activa, actualiza el estado del medidor a `INSTALADO` dentro de una transacción atómica y audita la operación.
    - El servicio `desasignar_medidor()` exige la `lectura_retiro` (que no puede ser menor a la lectura de instalación), marca la asignación como `activo = False`, registra la fecha y motivo de retiro, cambia el estado del medidor a `DISPONIBLE` o `MANTENIMIENTO` y audita la acción.

---

### DEC-011: Estructura de Tarifario y Bloqueo de Retroactividad (R-DOM-10)
- **Contexto:** La tarifa se compone de una tarifa básica con consumo mínimo incluido y un esquema de tramos por volumen excedente. Todo cambio tarifario rige exclusivamente para el futuro.
- **Implementación Técnica:**
  - Modelo `Tarifario`:
    - Campos: `nombre`, `servicio` (FK a Servicio de Agua Potable), `categoria` (`DOMESTICO`, `COMERCIAL`, `INDUSTRIAL`, `SOCIAL`), `tarifa_basica` (`DECIMAL(10,2)`), `consumo_minimo_m3` (`DECIMAL(10,2)`), `precio_adicional_m3` (`DECIMAL(10,2)`), `fecha_vigencia_desde` (Date), `fecha_vigencia_hasta` (Date, null=True), `activo` (Boolean).
  - Modelo `TramoTarifario`:
    - Campos: `tarifario` (FK), `orden` (PositiveSmallIntegerField), `desde_m3` (Decimal), `hasta_m3` (Decimal, null=True para tramo abierto), `precio_unitario` (Decimal), `es_valor_fijo` (Boolean, default=False).
  - **Resolución Determinística:** Un método de servicio `obtener_tarifa_vigente(servicio, categoria, fecha)` busca el tarifario cuya vigencia contenga la fecha del periodo (`fecha_vigencia_desde <= fecha AND (fecha_vigencia_hasta IS NULL OR fecha_vigencia_hasta >= fecha)`).
  - **Inmutabilidad y Snapshot:** Cuando se generen obligaciones en la Fase 3, la obligación almacenará una copia congelada (`snapshot`) de la tarifa y los tramos calculados, garantizando que futuros cambios o inactivaciones de tarifas no modifiquen retroactivamente deudas devengadas (R-DOM-10).

---

### DEC-012: Generador de Códigos Correlativos Seguros
- **Contexto:** Los socios y medidores requieren códigos internos legibles e inequívocos (ej. `SOC-0001`, `MED-0001`).
- **Implementación Técnica:**
  - Servicio `generar_codigo_socio()` y `generar_codigo_medidor()` que consultan el último correlativo registrado con bloqueo pesimista en caso de concurrencia o calculan el `MAX(id) + 1` formateado con ceros a la izquierda (relleno de 4 a 6 dígitos).
  - Se permite además la personalización o ingreso manual de código si la institución ya tiene códigos físicos previos, validando siempre unicidad estricta (`unique=True`).

---

### DEC-013: Cédula de Identidad Boliviana con Complemento Único
- **Contexto:** En el padrón boliviano existen personas con el mismo número de CI pero diferenciadas por un complemento alfanumérico (ej. `4920192` y `4920192-1A`).
- **Implementación Técnica:**
  - El modelo `Socio` almacena `ci` (`CharField(max_length=20)`) y `ci_complemento` (`CharField(max_length=5, blank=True, default='')`).
  - Se establece una restricción de unicidad compuesta `UniqueConstraint(fields=['ci', 'ci_complemento'], name='unique_socio_ci_complemento')`.
  - Si el socio no tiene complemento, `ci_complemento` es cadena vacía, garantizando la unicidad para personas con CI simple y compatibilidad total con homónimos documentados.

---

### DEC-014: Prohibición de Borrado Físico y Desactivación en Cascada Controlada (P5)
- **Contexto:** Ninguna entidad de datos maestros (`Zona`, `Socio`, `Servicio`, `Medidor`) puede borrarse físicamente si tiene registros asociados.
- **Implementación Técnica:**
  - Todas las entidades heredan de `BaseAuditableModel` (`apps.core.models`), proveyendo los campos `activo`, `creado_en`, `actualizado_en` y el borrado lógico.
  - Sobrescribir el método `delete()` en los modelos para impedir llamadas a `DELETE` físico: lanza `ValidationError("No está permitido eliminar físicamente registros de datos maestros. Utilice la desactivación lógica.")`.
  - Vistas y formularios proveen la opción de inactivar (`activo = False`), registrando motivo y trazabilidad en la bitácora.

