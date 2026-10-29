# Especificación Funcional: Fase 6 - Reportes Administrativos y Financieros (006-reportes-administrativos-financieros)

## 1. Identificación y Metadatos
- **Módulo**: Grupo 10: Reportes (Secciones 10.1..10.7 y 15 de la fuente funcional).
- **Ruta principal**: `/reportes/`
- **Estado**: Aprobado para implementación
- **Prioridad**: Crítica (Fase 6 del roadmap canónico de implementación)
- **Trazabilidad Constitucional**: P1, P2, P5, P6, P7, P8.

---

## 2. Descripción General y Objetivos
Este módulo consolida la inteligencia administrativa, operativa y financiera de SisAgua. Permite a los directivos, administradores y auditores del comité/cooperativa disponer de información verídica, no duplicada y transparente derivada de los datos transaccionales del sistema (Principio P2 - Fuente Única de Verdad).

### Objetivos Clave
1. Generar el **Reporte Consolidado de Deudores** (Sección 10.1), sumando obligaciones pendientes reales, distinguiendo agua, membresía y otros conceptos, calculando antigüedad y excluyendo conceptos saldados o anulados.
2. Proveer el **Reporte de Recaudación Financiera Efectiva** (Sección 10.5), desglosando ingresos diarios, mensuales o por rango por medio de pago (`EFECTIVO`, `QR`, `TRANSFERENCIA`), cajero y servicio, distinguiendo recibos emitidos de recibos anulados.
3. Facilitar el **Reporte de Consumo de Agua Potable** (Sección 10.4), con volumen total consumido ($m^3$), promedios por medidor/zona, medidores sin lectura y lecturas anómalas u observadas.
4. Proveer el **Reporte Integral por Zona** (Sección 10.2), con padrón activo/inactivo, parque de medidores, facturación vs recaudación y mora.
5. Controlar el **Reporte de Membresías** (Sección 10.6), cuantificando ingresos por afiliaciones únicas, socios al día y membresías pendientes.
6. Habilitar la consulta y emisión del **Estado de Cuenta Individual 360°** (Sección 10.3), reflejando facturado vs pagado vs saldo pendiente.
7. Proveer capacidades de exportación a CSV y visualización membretada para impresión física en todos los informes.

---

## 3. Historias de Usuario y Criterios de Aceptación (Gherkin)

### US-REP-01: Reporte Consolidado de Deudores (Sección 10.1)
**Como** Administrador o Junta Directiva  
**Quiero** consultar el listado de socios con obligaciones pendientes  
**Para** conocer la cartera en mora clasificada por zona, concepto (agua, membresía) y antigüedad.

#### Escenarios de Aceptación
```gherkin
Scenario: Consulta de deudores con desglose por concepto
  Given que existen obligaciones pendientes en el sistema
  When el usuario accede al reporte de deudores
  Then el sistema muestra para cada socio:
    | Código | CI | Nombre Completo | Zona | Medidores | Deuda Agua | Deuda Membresía | Total Pendiente | Importe Vencido | Antigüedad (meses) |
  And suma los totales generales sin duplicar registros
  And excluye obligaciones con estado PAGADA o ANULADA

Scenario: Filtro por zona y meses de mora
  Given socios con 1, 2 y 4 meses de mora en distintas zonas
  When se filtra por zona "ZONA-NORTE" y mora mayor a 3 meses
  Then el reporte despliega únicamente los socios que cumplen ambos criterios
```

---

### US-REP-02: Reporte de Recaudación Financiera Efectiva (Sección 10.5)
**Como** Tesorero y Auditor  
**Quiero** consultar los ingresos efectivamente cobrados en caja en un rango de fechas  
**Para** conciliar la recaudación real por forma de pago, cajero y concepto.

#### Escenarios de Aceptación
```gherkin
Scenario: Cuadre de recaudación por medio de pago
  Given cobros registrados en el día por Bs 1.500 en Efectivo, Bs 800 en QR y Bs 300 en Transferencia
  And un recibo emitido por Bs 200 que fue formalmente ANULADO
  When el tesorero genera el reporte de recaudación del día
  Then el sistema desglosa:
    | Efectivo: Bs 1.500 | QR: Bs 800 | Transferencia: Bs 300 | Total Neto Cobrado: Bs 2.600 |
  And reporta por separado los Bs 200 del recibo anulado sin sumarlos al total neto
```

---

### US-REP-03: Reporte de Consumo y Monitoreo de Anomalías (Sección 10.4)
**Como** Responsable Técnico de Agua  
**Quiero** analizar el consumo mensual de agua por zona y detectar medidores con lecturas observadas  
**Para** verificar la demanda volumétrica de la red y ordenar revisiones en campo.

#### Escenarios de Aceptación
```gherkin
Scenario: Análisis de consumo del periodo
  Given lecturas registradas para el periodo "2026-02"
  When el usuario consulta el reporte de consumo de dicho periodo
  Then el sistema calcula:
    | Consumo total facturado (m³) |
    | Consumo promedio por medidor (m³) |
    | Cantidad de medidores con consumo cero |
    | Listado de medidores con lecturas en estado OBSERVADA |
```

---

### US-REP-04: Reporte Integral por Zona (Sección 10.2)
**Como** Administrador del Comité  
**Quiero** visualizar la situación de cada sector territorial  
**Para** evaluar el nivel de cobertura, facturación, cobranza e índice de morosidad por barrio.

#### Escenarios de Aceptación
```gherkin
Scenario: Comparativa de zonas
  Given varias zonas registradas con socios y conexiones
  When se consulta el reporte por zona
  Then se presenta una tabla comparativa con:
    | Zona | Socios Activos | Inactivos | Medidores | Facturado (Bs) | Recaudado (Bs) | Deuda Pendiente (Bs) | % Eficacia Cobranza |
```

---

### US-REP-05: Reporte de Membresías y Afiliaciones (Sección 10.6)
**Como** Secretario de Actas y Tesorero  
**Quiero** controlar las cuotas de incorporación única pagadas y pendientes  
**Para** supervisar el cumplimiento estatutario de los socios de la organización.

#### Escenarios de Aceptación
```gherkin
Scenario: Cuantificación de membresías
  Given socios dados de alta en el sistema
  When se consulta el reporte de membresías
  Then el sistema muestra:
    | Total Socios | Membresías Generadas | Membresías Pagadas | Membresías Pendientes | Total Recaudado Afiliación (Bs) |
```

---

### US-REP-06: Exportación a CSV y Vista Membretada Imprimible (Sección 10.7)
**Como** Usuario con permiso `REPORTES:EXPORTAR`  
**Quiero** descargar los reportes en CSV o imprimirlos con el membrete oficial del comité  
**Para** archivar constancias físicas y respaldar informes ante la asamblea general.

#### Escenarios de Aceptación
```gherkin
Scenario: Descarga de archivo CSV
  Given un usuario con permiso REPORTES:EXPORTAR
  When solicita cualquier reporte agregando ?format=csv
  Then el sistema devuelve un archivo CSV codificado en UTF-8 con cabeceras completas
  And registra el evento en BitacoraAuditoria (P6)
```

---

## 4. Reglas de Negocio Protegidas
- **P2 (Fuente única de verdad)**: Cero datos inventados o no reconciliados. Todos los totales se calculan directamente desde las tablas `Obligacion`, `Pago`, `Recibo` y `Lectura`.
- **P7 (Seguridad por defecto)**: Server-side RBAC con permisos `REPORTES:VER` y `REPORTES:EXPORTAR`.
- **P8 (Transparencia financiera)**: Distinción contable estricta entre importe facturado, importe cobrado, saldos pendientes y conceptos anulados.

