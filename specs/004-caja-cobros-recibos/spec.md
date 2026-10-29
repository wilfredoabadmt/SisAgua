# Especificación Funcional: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## 1. Identificación y Metadatos
- **Módulo**: Grupo 9: Caja, cobros y recibos (Secciones 2.4, 9.1..9.5 de la fuente funcional).
- **Ruta principal**: `/caja/`
- **Estado**: Aprobado para implementación
- **Prioridad**: Crítica (Fase 4 del roadmap de implementación canónico)
- **Trazabilidad Constitucional**: P1, P2, P3, P4, P5, P6, P7, P8, R-DOM-15, R-DOM-16, R-DOM-17.

---

## 2. Descripción General y Objetivos
Este módulo implementa el subsistema de cobranza en ventanilla, emisión de recibos oficiales inalterables, gestión de turnos de caja con arqueo físico y reversión autorizada de cobros. Constituye el núcleo de recaudación financiera del Sistema de Administración, Consumo y Cobro de Agua Potable (**SisAgua**).

### Objetivos Clave
1. Proporcionar una ventanilla de cobranza ágil con búsqueda multidimensional de socios (código, nombre, CI, medidor).
2. Garantizar la regla de negocio inviolable de **cero pagos parciales por obligación individual** (R-DOM-15).
3. Permitir el cobro multiconcepto unificado (consumo de agua de múltiples meses/medidores, membresías pendientes, reconexiones u otros servicios autorizados) en una única transacción ACID blindada contra condiciones de carrera concurrentes (R-DOM-16).
4. Emitir el Recibo Oficial de Cobranza correlativo, cronológico, inalterable y con código QR de autenticidad (R-DOM-17).
5. Proveer un flujo de anulación restringido a supervisores que exija justificación documentada y revierta automáticamente las obligaciones al estado `PENDIENTE` sin destruir registros históricos (P5, R-DOM-17).
6. Implementar el control operativo de sesiones/turnos de caja (`CajaTurno`) con registro de fondo de cambio, cálculo automatizado de arqueo por medio de pago y registro de diferencias.

---

## 3. Historias de Usuario y Criterios de Aceptación (Gherkin)

### US-CAJA-01: Búsqueda de Socio en Ventanilla y Consulta de Deudas
**Como** Cajero u Operador de Ventanilla  
**Quiero** buscar a un socio por su código, nombre, CI o número de serie de medidor  
**Para** visualizar el estado consolidado de su cuenta, sus obligaciones pendientes (distinguiendo vencidas y vigentes) y su historial reciente de pagos.

#### Escenarios de Aceptación
```gherkin
Scenario: Búsqueda exitosa de socio por código o CI
  Given que el cajero tiene un turno de caja abierto
  When ingresa el término "SOC-0001" o el CI "4567890" en la ventanilla de cobro
  Then el sistema localiza al socio y despliega:
    | Ficha básica (código, nombre completo, CI, zona, medidores) |
    | Resumen de saldo total pendiente y obligaciones vencidas |
    | Listado detallado de obligaciones pendientes seleccionables |
    | Historial de los últimos recibos emitidos al socio |

Scenario: Búsqueda sin coincidencias
  Given que el cajero ingresa un criterio inexistente "NOEXISTE999"
  When ejecuta la búsqueda
  Then el sistema muestra un mensaje informativo indicando que no se encontraron socios con ese criterio
```

---

### US-CAJA-02: Selección Multiconcepto y Prohibición Estricta de Pagos Parciales (R-DOM-15)
**Como** Administrador y Responsable de Caja  
**Quiero** que el cajero pueda seleccionar una o varias obligaciones completas del socio  
**Para** liquidarlas simultáneamente, impidiendo terminantemente que se fraccione el monto de una obligación individual o se liquide parcialmente.

#### Escenarios de Aceptación
```gherkin
Scenario: Selección de múltiples obligaciones completas
  Given que el socio tiene:
    | Periodo | Concepto | Monto | Saldo |
    | 2026-01 | Consumo Agua Enero | 35.00 | 35.00 |
    | 2026-02 | Consumo Agua Febrero | 40.00 | 40.00 |
    | MEMBRESIA | Cuota de Afiliación | 100.00 | 100.00 |
  When el cajero marca las obligaciones de Enero y Membresía
  Then el sistema calcula la suma exacta no editable: Bs 135.00
  And la obligación de Febrero permanece pendiente con Bs 40.00

Scenario: Bloqueo de cobro con importe modificado o parcial (R-DOM-15)
  Given que el cajero intenta enviar una solicitud modificando el importe a cobrar para abonar 20.00 a la obligación de Enero (de 35.00)
  When el servidor procesa la solicitud
  Then la operación es rechazada con error de validación
  And ninguna obligación es modificada
```

---

### US-CAJA-03: Procesamiento Atómico de Cobro y Emisión de Recibo Inalterable (R-DOM-16, R-DOM-17)
**Como** Cajero  
**Quiero** procesar el cobro de las obligaciones seleccionadas especificando la forma de pago (Efectivo, QR o Transferencia)  
**Para** liquidar la deuda, actualizar el estado de cuenta y emitir el Recibo Oficial correlativo e inalterable.

#### Escenarios de Aceptación
```gherkin
Scenario: Cobro exitoso en transacción atómica con select_for_update()
  Given que el cajero tiene un turno de caja abierto
  And las obligaciones seleccionadas están en estado PENDIENTE
  When confirma el cobro con método "EFECTIVO" y monto exacto
  Then se ejecuta una transacción ACID donde:
    | Se bloquean concurrentemente las filas de las obligaciones (select_for_update) |
    | Cada obligación seleccionada pasa a estado PAGADA con saldo_pendiente = 0.00 |
    | Se genera un registro de Pago asociado al turno del cajero |
    | Se genera un Recibo con número correlativo institucional único (ej. REC-2026-000001) |
    | Se generan los DetalleRecibo con snapshot de cada concepto |
    | Se registra el evento en BitacoraAuditoria con usuario, fecha e IP |
  And el sistema redirige a la vista de impresión del recibo oficial
```

---

### US-CAJA-04: Anulación Autorizada de Recibo y Reversión Automática (R-DOM-17, P5)
**Como** Supervisor o Administrador de Caja  
**Quiero** anular un recibo erróneamente emitido mediante un flujo formal y justificado  
**Para** que las obligaciones involucradas se restablezcan íntegramente al estado PENDIENTE sin eliminar físicamente el recibo.

#### Escenarios de Aceptación
```gherkin
Scenario: Anulación autorizada con motivo obligatorio
  Given que un usuario con permiso CAJA:ANULAR visualiza un recibo EMITIDO
  When solicita la anulación e ingresa el motivo "Error en selección de conceptos a solicitud del socio"
  Then el sistema actualiza el recibo:
    | Estado pasa a ANULADO |
    | Se registra usuario_anulacion, fecha_anulacion y motivo_anulacion |
    | Todas las obligaciones saldadas por dicho recibo vuelven a PENDIENTE con su saldo íntegro |
    | El registro del Recibo y sus Detalles permanecen en la base de datos (DELETE prohibido P5) |
    | Se audita la anulación en BitacoraAuditoria |

Scenario: Rechazo de anulación por usuario no autorizado o sin motivo
  Given un usuario sin permiso CAJA:ANULAR o una solicitud sin motivo justificado
  When intenta anular un recibo
  Then la operación es rechazada con código 403 Forbidden o error de validación
```

---

### US-CAJA-05: Control de Turnos de Caja, Arqueo y Cierre (Sección 9.5)
**Como** Cajero y Administrador  
**Quiero** abrir un turno de caja con fondo inicial, registrar cobros asociados y realizar el arqueo físico al finalizar la jornada  
**Para** verificar la concordancia entre los importes declarados físicamente y los cobros registrados por el sistema.

#### Escenarios de Aceptación
```gherkin
Scenario: Apertura de turno de caja
  Given que el cajero no tiene turnos activos
  When abre turno ingresando un fondo inicial de Bs 100.00
  Then se crea el registro CajaTurno en estado ABIERTA
  And el cajero queda habilitado para registrar cobros

Scenario: Cobro bloqueado si no hay turno abierto
  Given que el cajero no ha abierto turno o su turno anterior está CERRADO
  When intenta procesar un cobro
  Then el sistema bloquea la operación y exige la apertura previa de turno

Scenario: Arqueo y cierre de turno
  Given un turno abierto con:
    | Cobros efectivo sistema: Bs 350.00 |
    | Cobros QR/Transferencia sistema: Bs 120.00 |
    | Fondo inicial: Bs 100.00 |
    | Total efectivo esperado en gaveta: Bs 450.00 |
  When el cajero declara Bs 450.00 en efectivo en su arqueo físico
  Then el sistema calcula una diferencia de Bs 0.00
  And marca el turno como CERRADO con fecha y hora de cierre
  And se genera el reporte de arqueo imprimible
```

---

## 4. Reglas de Negocio Protegidas
- **R-DOM-15 (Prohibición de pagos parciales)**: No se admite amortización fraccionada por obligación. Cada obligación se paga al 100%.
- **R-DOM-16 (Cobro multiconcepto y atomicidad)**: Liquidación de cualquier combinación de conceptos en un único bloque ACID pesimista (`select_for_update()`).
- **R-DOM-17 (Inalterabilidad del Recibo y Reversión)**: Recibo con correlativo institucional único. `DELETE` prohibido por P5. La anulación reabre las deudas automáticamente.
- **P7 (Seguridad Server-Side)**: Verificación obligatoria de permisos (`CAJA:VER`, `CAJA:CREAR`, `CAJA:CERRAR`, `CAJA:ANULAR`) en el backend.

