# Especificación Funcional: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 2 del Orden Canónico de Implementación (Fuente, Sección 15)  
> **Normativa Rector:** Constitución SDD v1.0 (`.specify/memory/constitution.md`)  
> **Fuente Funcional:** `SISTEMA DE ADMINISTRACION.docx` (Secciones 4.1, 5.1, 5.2, 5.3, 6.1 a 6.7)  
> **Estado:** APROBADA PARA IMPLEMENTACIÓN  

---

## 1. Resumen Ejecutivo y Objetivos de Negocio

La Fase 2 establece los cimientos del dominio de agua potable comunitaria para SisAgua en Bolivia. Reemplaza los registros dispersos en cuadernos, carpetas físicas y planillas de cálculo mediante un modelo relacional estricto que gobierna:

1. **Zonas y Sectores Territoriales:** Localización física de predios y organización de rutas de lectura y cobranza.
2. **Catálogo de Servicios:** Parametrización de modalidades de cobro (por lectura/volumétrica, cuota fija mensual, pago único/membresía y eventual).
3. **Padrón Oficial de Socios:** Control riguroso de identidad (CI único), codificación correlativa y **generación atómica de la membresía única** como derecho de afiliación patrimonial.
4. **Parque de Medidores y Asignaciones:** Inventario de dispositivos físicos, control de exclusividad de asignación (un medidor a un solo socio activo simultáneamente) y registro obligatorio de lecturas de instalación y retiro.
5. **Estructura Tarifaria Paramétrica:** Definición de tarifas básicas, consumos mínimos incluidos, tramos escalonados y vigencias temporales con bloqueo absoluto de retroactividad sobre obligaciones pasadas.

---

## 2. Marco Normativo Constitucional Aplicable

Esta especificación se encuentra sujeta a los siguientes principios y reglas constitucionales innegociables:

| Código | Principio / Regla | Mandato en Fase 2 |
|---|---|---|
| **P1** | Fidelidad de Negocio | No se alteran fórmulas ni modalidades de cobro sin respaldo formal. |
| **P2** | Fuente Única de Verdad | Cada medidor, socio y servicio tiene una identidad unívoca y auditada. |
| **P3** | Integridad Financiera | La creación del socio y su derecho de membresía ocurren en una sola transacción ACID. |
| **P4** | Idempotencia | Reintentar el alta o la asignación no duplica registros ni membresías. |
| **P5** | Conservación Histórica | Prohibición absoluta de sentencias `DELETE`. Se utiliza borrado lógico (`activo = False`). |
| **P6** | Auditoría Verificable | Toda alta, cambio de estado, sustitución de medidor o cambio tarifario se audita con usuario, IP y delta. |
| **P7** | Seguridad por Defecto | RBAC en servidor: solo perfiles autorizados pueden modificar el padrón o las tarifas. |
| **R-DOM-01** | Unicidad de Identidad | Código de socio único del sistema y CI único por institución. |
| **R-DOM-02** | Multi-medición | Un socio puede tener uno o varios medidores asignados en una o más zonas. |
| **R-DOM-03** | Exclusividad de Asignación | Un medidor físico solo puede estar asignado a un socio activo a la vez. |
| **R-DOM-04** | Trazabilidad de Sustitución | El retiro de un medidor exige lectura final; la instalación exige lectura inicial. |
| **R-DOM-05** | Inmutabilidad de Estados | Inactivar o suspender un socio no destruye sus datos ni extingue sus deudas. |
| **R-DOM-10** | No Retroactividad Tarifaria | Las modificaciones tarifarias aplican hacia el futuro según fecha de vigencia. |
| **R-DOM-13** | Independencia de Membresía | La membresía es única por socio, no recurrente mensualmente, emitida al alta. |
| **R-DOM-14** | Vencimiento Determinístico | Fecha de vencimiento computada con día institucional o fin de mes. |

---

## 3. Historias de Usuario

### US1: Gestión de Zonas y Sectores (Prioridad: ALTA)
**Como** Administrador del Sistema  
**Quiero** registrar y consultar las zonas, sectores o barrios de la comunidad  
**Para** agrupar los predios de los socios y ordenar las rutas de medición y cobro.

- **Criterios de Aceptación:**
  - Código de zona alfanumérico único por institución (ej. `ZON-01`, `CENTRO`).
  - Nombre de la zona obligatorio (ej. `Zona Central`, `Barrio Lindo`).
  - Nombre del responsable o delegado de zona (opcional).
  - Bloqueo de eliminación física: si una zona tiene socios o medidores vinculados, no puede eliminarse ni inactivarse sin advertencia; nunca se ejecuta `DELETE`.
  - Auditoría automática de creación y actualización.

---

### US2: Catálogo de Servicios y Modalidades de Cobro (Prioridad: ALTA)
**Como** Administrador o Directorio  
**Quiero** configurar el catálogo de servicios que ofrece la organización y su modalidad de cobro  
**Para** soportar agua potable medida, cuotas fijas de mantenimiento, recojo de basura y conceptos eventuales.

- **Criterios de Aceptación:**
  - Código único de servicio (ej. `SERV-AGUA`, `SERV-MEMB`, `SERV-BAS`).
  - Nombre descriptivo y descripción ampliada.
  - Modalidad de cobro catalogada:
    - `LECTURA_VOLUMETRICA`: Cobro según diferencia de lecturas ($m^3$).
    - `CUOTA_FIJA_MENSUAL`: Monto fijo periódico independiente del consumo.
    - `PAGO_UNICO_MEMBRESIA`: Concepto único generado al afiliarse el socio.
    - `EVENTUAL`: Cobro esporádico (conexión, reconexión, multas aprobadas).
  - Estado activo/inactivo (borrado lógico).

---

### US3: Padrón Oficial de Socios con Alta Atómica de Membresía (Prioridad: CRÍTICA)
**Como** Encargado de Registro o Administrador  
**Quiero** dar de alta a un nuevo socio con sus datos de identidad, domicilio y zona  
**Para** incorporarlo formalmente a la comunidad y generar automáticamente su obligación de membresía única.

- **Criterios de Aceptación:**
  - Generación de código de socio único e incremental (ej. `SOC-0001`).
  - Cédula de Identidad (CI) obligatoria y única en la institución; soporte para complemento de CI boliviano (ej. `4892819-1A`).
  - Nombres y Apellidos obligatorios. Teléfono y Correo electrónico opcionales.
  - Selección obligatoria de Zona y registro de dirección/predio.
  - Estado del socio: `ACTIVO` (por defecto), `INACTIVO`, `SUSPENDIDO`, `RETIRADO`.
  - **Atomicidad de Membresía (R-DOM-13):** En la misma transacción `transaction.atomic()`, al crearse el socio se genera una única `Obligacion` de tipo membresía con el monto oficial configurado en la institución o en el servicio de membresía. Si la transacción falla, se revierte por completo.
  - Idempotencia: el sistema impide generar una segunda membresía para el mismo socio.

---

### US4: Parque de Medidores y Asignación Exclusiva (Prioridad: ALTA)
**Como** Encargado Técnico o Administrador  
**Quiero** inventariar los medidores físicos y asignarlos a los predios de los socios  
**Para** llevar el control del activo físico y asegurar la medición individual del consumo.

- **Criterios de Aceptación:**
  - Código interno del medidor único (ej. `MED-001`).
  - Número de serie del fabricante obligatorio y único.
  - Marca, modelo y diámetro en pulgadas/mm.
  - Lectura inicial de calibración/fábrica en $m^3$ (no negativa, decimal exacto `DECIMAL(10,2)`).
  - Estado operativo: `DISPONIBLE`, `INSTALADO`, `MANTENIMIENTO`, `RETIRADO`, `DE_BAJA`.
  - **Exclusividad de Asignación (R-DOM-03):** Un medidor solo puede estar asignado a un socio activo a la vez. No se permite asignación concurrente. Al asignarse, el medidor pasa automáticamente a estado `INSTALADO`.
  - Un socio puede tener múltiples medidores asignados (R-DOM-02).

---

### US5: Trazabilidad de Sustitución y Retiro de Medidores (Prioridad: ALTA)
**Como** Técnico de Operaciones  
**Quiero** registrar el retiro o cambio de un medidor averiado por uno nuevo  
**Para** conservar el historial de lecturas finales y asegurar continuidad en la facturación sin perder datos históricos.

- **Criterios de Aceptación:**
  - Al retirar o desasignar un medidor, es obligatorio registrar la `lectura_retiro` ($m^3$) y el motivo (avería, cambio de titular, baja de conexión).
  - El medidor saliente cambia a estado `MANTENIMIENTO` o `RETIRADO`.
  - El registro histórico de la asignación previa retiene: fecha de inicio, fecha de fin, lectura de instalación y lectura de retiro (R-DOM-04).
  - No se borra ninguna lectura ni obligación previa vinculada a dicho medidor.

---

### US6: Tarifario Multitramo y Bloqueo de Retroactividad (Prioridad: ALTA)
**Como** Directorio o Administrador  
**Quiero** configurar las tarifas de agua por categoría con sus tramos escalonados y fechas de vigencia  
**Para** aplicar el cálculo de consumo exacto según las resoluciones de la Asamblea.

- **Criterios de Aceptación:**
  - Nombre del tarifario (ej. `Tarifario General Doméstico 2026`).
  - Servicio asociado (por defecto `Agua Potable`).
  - Categoría: `DOMESTICO`, `COMERCIAL`, `INDUSTRIAL`, `SOCIAL`.
  - Tarifa básica (Bs) y Consumo mínimo incluido ($m^3$) (ej. Bs 10.00 por 10 $m^3$).
  - Precio por metro cúbico adicional o tramos específicos parametrizables.
  - Fecha de vigencia desde (obligatoria) y fecha de vigencia hasta (nula mientras siga vigente).
  - **No Retroactividad (R-DOM-10):** Crear un nuevo tarifario o modificar fechas no recalcula ni altera deudas ni recibos ya emitidos. Las obligaciones retienen el snapshot del tarifario aplicado.

---

### US7: Ficha Integral 360° del Socio (Prioridad: MEDIA)
**Como** Cajero, Operador o Administrador  
**Quiero** consultar la ficha integral de un socio  
**Para** visualizar en una sola pantalla sus datos personales, su zona, todos sus medidores asignados con su estado y sus obligaciones pendientes.

- **Criterios de Aceptación:**
  - Muestra datos personales, CI, teléfono, zona y dirección.
  - Lista de medidores actualmente asignados (código, serie, lectura inicial, fecha instalación).
  - Historial de medidores anteriores desasignados.
  - Resumen de obligaciones pendientes de pago (membresía, agua, otros servicios).
  - Botones de acción contextuales según permisos RBAC (`SOCIOS:EDITAR`, `MEDIDORES:ASIGNAR`, etc.).

---

## 4. Requisitos Funcionales (FR)

- **FR-001 (Zonas CRUD):** El sistema debe permitir crear, listar, editar y desactivar lógicamente zonas territoriales con código único alfanumérico.
- **FR-002 (Bloqueo de eliminación en Zonas):** El sistema debe impedir la eliminación física de zonas. Si se intenta desactivar una zona con socios activos, debe solicitar confirmación explícita.
- **FR-003 (Servicios CRUD):** El sistema debe catalogar servicios con su modalidad de cobro (`LECTURA_VOLUMETRICA`, `CUOTA_FIJA_MENSUAL`, `PAGO_UNICO_MEMBRESIA`, `EVENTUAL`).
- **FR-004 (Socios CRUD):** El sistema debe registrar socios garantizando unicidad de CI y código de socio por institución.
- **FR-005 (Complemento CI):** El sistema debe soportar CI con complemento opcional para evitar colisiones de números de carnet en Bolivia.
- **FR-006 (Alta Atómica de Membresía):** Toda creación de socio debe generar en la misma transacción ACID una obligación de membresía única por el valor configurado.
- **FR-007 (Idempotencia de Membresía):** El sistema debe impedir la creación de más de una obligación de membresía para el mismo socio y servicio.
- **FR-008 (Medidores Inventario):** El sistema debe registrar medidores con código interno único, número de serie único, marca, modelo y lectura inicial $\ge 0$.
- **FR-009 (Exclusividad de Medidor):** El sistema debe rechazar la asignación de un medidor que ya se encuentre asignado a otro socio en estado activo.
- **FR-010 (Multi-medidor por Socio):** El sistema debe permitir que un socio tenga simultáneamente 1 a $N$ medidores asignados.
- **FR-011 (Retiro de Medidor):** Al desasignar un medidor, el sistema debe registrar obligatoriamente la fecha de retiro, la lectura final y el motivo del retiro.
- **FR-012 (Tarifario Base):** El sistema debe permitir registrar tarifas por categoría con tarifa básica, consumo mínimo incluido y precio adicional por $m^3$.
- **FR-013 (Tramos Tarifarios):** El sistema debe permitir definir tramos escalonados con límites inferior y superior en $m^3$ y precio unitario aplicable.
- **FR-014 (Vigencia Tarifaria):** El sistema debe gestionar fechas de vigencia y resolver de forma determinística la tarifa activa para una fecha dada.
- **FR-015 (Inmutabilidad de Tarifas Aplicadas):** Los cambios en el tarifario nunca modificarán obligaciones devengadas con anterioridad.
- **FR-016 (Estados de Socio):** El sistema debe permitir transicionar socios entre `ACTIVO`, `INACTIVO`, `SUSPENDIDO` y `RETIRADO`.
- **FR-017 (Preservación de Deudas):** La inactivación de un socio no cancela ni suprime sus deudas pendientes.
- **FR-018 (Ficha del Socio):** El sistema debe proveer una vista consolidada de datos del socio, medidores vinculados y estado financiero.
- **FR-019 (Auditoría Integral):** Toda operación de creación, edición, asignación, retiro y cambio de estado debe registrarse en `BitacoraAuditoria`.
- **FR-020 (Validación RBAC en Servidor):** Cada endpoint o vista de Fase 2 debe validar permisos específicos (`ZONAS:VER`, `ZONAS:CREAR`, `SOCIOS:VER`, `SOCIOS:CREAR`, `MEDIDORES:ASIGNAR`, `TARIFAS:ADMIN`).

---

## 5. Requisitos No Funcionales (NFR)

- **NFR-001 (Tipos Monetarios):** Todos los valores monetarios deben almacenarse y procesarse en tipo `DECIMAL(12,2)`. Queda terminantemente prohibido el uso de flotantes (`float/double`).
- **NFR-002 (Cero Borrado Físico):** Ninguna tabla de datos maestros ejecutará sentencias SQL `DELETE`. Toda eliminación es una desactivación lógica (`activo = False`).
- **NFR-003 (Rendimiento en Búsqueda):** La búsqueda de socios por CI, código o apellido debe responder en menos de 200 ms con índices optimizados sobre hasta 50,000 registros.
- **NFR-004 (Mobile-First y Responsive):** Las vistas de consulta y asignación deben adaptarse a teléfonos inteligentes y tabletas de operadores de campo.
- **NFR-005 (Transaccionalidad ACID):** Las operaciones de alta de socio con membresía y de reasignación de medidores deben ejecutarse en bloques atómicos con aislamiento estricto.

---

## 6. Criterios de Éxito y Aceptación (SC)

- **SC-001:** Se registran zonas y se bloquea la eliminación física de zonas con medidores o socios asociados.
- **SC-002:** Se registra un nuevo socio y de forma atómica e indivisible se genera exactamente una obligación de membresía única no recurrente.
- **SC-003:** Se intenta registrar un socio con un CI ya existente y el sistema lo rechaza con mensaje de validación claro.
- **SC-004:** Se asigna un medidor a un socio exitosamente, y se verifica que dicho medidor no puede ser asignado simultáneamente a otro socio.
- **SC-005:** Se desasigna un medidor registrando la lectura de retiro, quedando el medidor disponible para una nueva asignación y conservando el historial.
- **SC-006:** Se configura un tarifario con tramos y se verifica que no altera obligaciones previamente existentes.
- **SC-007:** Cobertura de pruebas automatizadas del 100% en los flujos críticos de Fase 2 aprobada con `pytest`.

