# SisAgua — Sistema de Administración, Consumo y Cobro de Agua Potable

Plataforma integral desarrollada en estricto cumplimiento del documento funcional primario de 40 páginas (`SISTEMA DE ADMINISTRACION.docx`, 882 párrafos), la **Constitución SDD v1.0** y el marco regulatorio boliviano (Ley N° 2066 y directrices de la AAPS). Orientada a Comités de Agua Potable y Saneamiento (CAPYS), cooperativas de servicios públicos y asociaciones comunitarias en Bolivia.

> **Estado del Proyecto:** **100% COMPLETADO Y CERTIFICADO (112/112 Tests PASS)**  
> **Metodología:** Spec-Driven Development (SDD / Spec Kit)  
> **Constitución Oficial:** [.specify/memory/constitution.md](.specify/memory/constitution.md) | [CONSTITUCION_SDD_v1.0.md](CONSTITUCION_SDD_v1.0.md)  
> **Guía Operativa:** [CLAUDE.md](CLAUDE.md)

---

## 1. Resumen de Fases Canónicas Implementadas y Certificadas

| Fase | Feature | Descripción Normativa | Tests | Estado |
|---|---|---|:---:|:---:|
| **Fase 1** | `001-configuracion-seguridad` | Singleton institucional, Custom User Model, Argon2id, RBAC server-side, forzado de clave temporal y auditoría inalterable sanitizada. | 20 | PASS |
| **Fase 2** | `002-datos-maestros` | Zonas territoriales, Socios con CI boliviano y complemento, alta atómica con membresía única (R-DOM-13), tarifarios escalonados sin retroactividad (R-DOM-10), parque de medidores y asignación exclusiva (R-DOM-03). | 27 | PASS |
| **Fase 3** | `003-consumo-lecturas-calculo` | Toma mensual de lecturas, validación de monotonicidad (R-DOM-07), proforma informativa de medición (R-DOM-09) y motor determinístico de facturación mensual idempotente (R-DOM-11/12/14). | 14 | PASS |
| **Fase 4** | `004-caja-cobros-recibos` | Control de turnos y arqueos con registro de diferencias, prohibición de pagos parciales (R-DOM-15), cobro multiconcepto ACID con `select_for_update()` (R-DOM-16), recibo oficial correlativo (`REC-YYYY-000001`) con QR y literal boliviano, anulación autorizada con reversión lógica íntegra (R-DOM-17, P5). | 14 | PASS |
| **Fase 5** | `005-transcripcion-historica-regularizacion` | Lotes de digitalización, máquina de estados (`PENDIENTE` a `MIGRADO`), distinción entre lectura histórica informativa y deuda exigible (R-DOM-18), regularización trazable de deudas históricas respaldadas (R-DOM-19) y reporte de migración. | 15 | PASS |
| **Fase 6** | `006-reportes-administrativos-financieros` | Reporte consolidado de deudores sin duplicados (Sección 10.1), reporte de recaudación neta efectiva por medio de pago (`EFECTIVO`, `QR`, `TRANSFERENCIA`) con discriminación de recibos anulados (Sección 10.5), análisis volumétrico de consumo y anomalías (Sección 10.4), balance territorial por zona (Sección 10.2), membresías (Sección 10.6), estado de cuenta individual 360° (Sección 10.3), membrete oficial `@media print` y exportación CSV protegida por RBAC (`REPORTES:EXPORTAR`). | 10 | PASS |
| **Fase 7** | `007-portal-individual-socios` | Portal individual de autoservicio para socios comunitarios (Sección 11), aislamiento estricto de identidad multitenant a nivel fila anti-IDOR (Principio P7, R-DOM-01), consulta de medidores y lecturas, proforma informativa mensual (R-DOM-09), recibos oficiales pagados y actualización autónoma de teléfono/correo. | 6 | PASS |
| **Fase 8** | `008-auditoria-final-puesta-en-marcha` | Auditoría automatizada de integridad de datos (`verificar_integridad_sistema`) conforme a las 9 reglas de la Sección 13, motor de respaldo institucional serializado con manifiesto y checksum SHA-256 (`backup_institucional`), y pruebas de fin de ciclo. | 6 | PASS |
| **Total** | **8 / 8 Fases Canónicas** | **Suite Completa de Integración y Regresión** | **112** | **100% PASS** |

---

## 2. Arquitectura del Sistema

```
SisAgua/
├── apps/
│   ├── configuracion/    # Parámetros institucionales singleton y menús dinámicos
│   ├── seguridad/        # Custom User Model, Argon2id, RBAC, roles y permisos
│   ├── core/             # BaseAuditableModel (P5), middleware de seguridad, BitacoraAuditoria (P6)
│   ├── socios/           # Zonas territoriales, padrón de socios, emisión de membresía
│   ├── servicios/        # Catálogo de servicios, tarifarios escalonados y obligaciones
│   ├── medidores/        # Parque de medidores y asignaciones exclusivas
│   ├── consumo/          # Captura de lecturas, proformas informativas y motor de facturación
│   ├── caja/             # Ventanilla de cobro, turnos, arqueos y recibos oficiales correlativos
│   ├── transcripcion/    # Digitalización de planillas físicas y regularización de deudas históricas
│   ├── reportes/         # Reportes analíticos ejecutivos, territoriales y exportadores CSV
│   └── portal/           # Portal autónomo de socios con aislamiento anti-IDOR
├── fixtures/
│   ├── seed_roles_permisos.json  # Roles (Administrador, Cajero, Lector, Transcriptor, Socio, Auditor)
│   ├── seed_datos_maestros.json  # Zonas, servicios base, tarifarios escalonados
│   └── seed_menus.json           # Menús del sistema parametrizados por permisos
├── templates/            # Plantillas HTML responsivas con soporte de impresión oficial
├── tests/                # Suite de pruebas automatizadas (112 tests unitarios e integrales)
├── backups/              # Destino de volcados y manifiestos con checksum SHA-256
└── specs/                # Especificaciones formales SDD de cada feature
```

---

## 3. Puesta en Marcha Rápida

### Requisitos Previos
- Python 3.10 o superior (certificado en Python 3.15.1)
- Pip y Entorno Virtual

### Instalación de Dependencias
```bash
python -m pip install -r requirements.txt
```

### Aplicación de Migraciones
```bash
python manage.py migrate
```

### Carga de Datos Semilla (Fixtures)
```bash
python manage.py loaddata fixtures/seed_roles_permisos.json
python manage.py loaddata fixtures/seed_datos_maestros.json
python manage.py loaddata fixtures/seed_menus.json
```

### Creación de Superusuario Administrador
```bash
python manage.py createsuperuser
```

### Ejecución del Servidor de Desarrollo
```bash
python manage.py runserver
```
Acceso a la plataforma administrativa: `http://127.0.0.1:8000/login/`  
Acceso al portal de socios: `http://127.0.0.1:8000/portal/`

---

## 4. Comandos de Gestión y Certificación

### Ejecución de Pruebas Automatizadas (100% Cobertura de Requisitos)
```bash
python -m pytest tests/
```

### Verificación de Integridad de la Base de Datos (Sección 13)
Audita que no existan socios duplicados, dobles asignaciones de medidores, lecturas duplicadas, descuadres de recibos ni fugas de secretos en auditoría:
```bash
python manage.py verificar_integridad_sistema
```

### Generación de Respaldo Institucional con Hash SHA-256
Exporta un volcado JSON íntegro de todas las entidades del sistema y genera un manifiesto con metadatos y checksum:
```bash
python manage.py backup_institucional --output-dir backups
```

---

## 5. Principios Constitucionales de SisAgua (Constitución SDD v1.0)
- **P1:** Primacía del Documento Funcional Oficial (`SISTEMA DE ADMINISTRACION.docx`).
- **P2:** Fuente Única de Verdad (cero tablas redundantes ni sincronizaciones frágiles).
- **P3:** Integridad Financiera y Determinismo Transaccional (ACID, redondeos exactos).
- **P4:** Idempotencia en Operaciones de Facturación y Cobro (prohibición de dobles cargos o cobros).
- **P5:** Conservación Histórica y Cero Borrado Físico (intercepción de `DELETE` en BD).
- **P6:** Auditoría Verificable y Sanitización (registro inmutable sin contraseñas ni tokens).
- **P7:** Autorización Granular en Servidor (RBAC forzoso en backend, aislamiento anti-IDOR).
- **P8:** Simplicidad y Mantenibilidad Comunitaria.
- **P9:** Separación Transcripción Histórica vs. Deuda Exigible (R-DOM-18 / R-DOM-19).
- **P10:** Validación Previa al Cálculo Tarifario (exclusión de lecturas observadas).
