# Plan de Implementación: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 1 — Planificación y Constitution Check  
> **Fecha:** Octubre 2026  
> **Estado:** APROBADO  

---

## 1. Constitution Check (Puerta Constitucional Obligatoria)

Antes de proceder a la creación de tareas e implementación, se evalúa la estricta alineación con los principios y reglas de la Constitución SDD v1.0:

| Regla / Principio | Criterio de Validación | Estado |
|---|---|:---:|
| **P1: Fidelidad de Negocio** | Fórmulas, modalidades de cobro y flujos de asignación se apegan 100% a la fuente documental (`SISTEMA DE ADMINISTRACION.docx`, secciones 4.1, 5.1, 5.2, 5.3, 6.1 a 6.7). | **PASS** |
| **P2: Fuente Única de Verdad** | Toda entidad maestra tiene identificadores únicos (código, CI, serie) y estados auditables. | **PASS** |
| **P3: Integridad Financiera** | El alta de socio y la generación de la membresía única se ejecutan en un solo bloque `transaction.atomic()`. | **PASS** |
| **P4: Idempotencia** | Constraints únicas impiden la duplicación de socios por CI, de medidores por serie y de membresías por socio. | **PASS** |
| **P5: Conservación Histórica** | Cero `DELETE` físico. Las entidades heredan `BaseAuditableModel` con borrado lógico (`activo = False`). | **PASS** |
| **P6: Auditoría Verificable** | Toda alta, cambio de estado, asignación y retiro se registra en `BitacoraAuditoria` con usuario, IP y delta de datos. | **PASS** |
| **P7: Seguridad por Defecto** | Validación estricta de RBAC del lado del servidor con `@requiere_permiso` en todas las vistas. | **PASS** |
| **R-DOM-01: Identidad Única** | Código de socio único correlativo y CI único con soporte de complemento en base de datos. | **PASS** |
| **R-DOM-02: Multi-medición** | Modelo `AsignacionMedidor` permite que un socio posea simultáneamente 1 a $N$ medidores. | **PASS** |
| **R-DOM-03: Exclusividad** | `UniqueConstraint(fields=['medidor'], condition=Q(activo=True))` impide asignar un medidor a dos socios al mismo tiempo. | **PASS** |
| **R-DOM-04: Trazabilidad** | Retiro de medidor exige obligatoriamente lectura final y preserva intactas las lecturas previas. | **PASS** |
| **R-DOM-05: Inmutabilidad** | Inactivar o suspender socio no altera sus obligaciones deudoras pendientes. | **PASS** |
| **R-DOM-10: No Retroactividad** | Tarifarios cuentan con rango de vigencia (`fecha_vigencia_desde`, `fecha_vigencia_hasta`) y no modifican deudas devengadas. | **PASS** |
| **R-DOM-13: Membresía Única** | Se genera exactamente una obligación de membresía al crear al socio; aislada de la facturación mensual. | **PASS** |

**Resultado del Constitution Check:** **CONFORME (100% PASS). Aprobado para descomposición en tareas e implementación.**

---

## 2. Arquitectura de Módulos y Paquetes

```
apps/
├── socios/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py        # Zona, Socio, EstadoSocio
│   ├── forms.py         # ZonaForm, SocioForm
│   ├── services.py      # registrar_socio (atómico + membresía), generar_codigo_socio
│   ├── views.py         # CRUD Zonas, CRUD Socios, Ficha 360°
│   ├── urls.py
│   └── templates/socios/
├── servicios/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py        # Servicio, Tarifario, TramoTarifario, Obligacion
│   ├── forms.py         # ServicioForm, TarifarioForm, TramoForm
│   ├── services.py      # resolver_tarifa_vigente, emitir_obligacion_membresia
│   ├── views.py         # Catálogo Servicios, Tarifarios y Tramos
│   ├── urls.py
│   └── templates/servicios/
└── medidores/
    ├── __init__.py
    ├── apps.py
    ├── models.py        # Medidor, AsignacionMedidor, EstadoMedidor
    ├── forms.py         # MedidorForm, AsignarMedidorForm, RetirarMedidorForm
    ├── services.py      # asignar_medidor, retirar_medidor, generar_codigo_medidor
    ├── views.py         # Inventario Medidores, Asignaciones, Retiros
    ├── urls.py
    └── templates/medidores/
```

---

## 3. Estrategia de Testing (Test-Driven Development)

Se desarrollará una suite exhaustiva de pruebas automáticas en `tests/`:

1. `tests/test_zonas.py`:
   - Alta de zona con código en mayúsculas y nombre obligatorio.
   - Bloqueo de códigos duplicados.
   - Inactivación lógica y prohibición de borrado físico si tiene socios.
   - Verificación de permisos RBAC (`ZONAS:VER`, `ZONAS:CREAR`).

2. `tests/test_servicios_tarifas.py`:
   - Catálogo de servicios con modalidades de cobro.
   - Creación de tarifario base con tramos escalonados.
   - Consulta de tarifa vigente por fecha y categoría.
   - Verificación de no retroactividad (R-DOM-10).

3. `tests/test_socios.py`:
   - Alta de socio con CI único y generación de código correlativo `SOC-XXXX`.
   - Rechazo de CI duplicado (con y sin complemento).
   - **Alta Atómica:** Verificación de creación del socio y emisión indivisible de la obligación de membresía única (R-DOM-13).
   - Verificación de no duplicación de membresía ante reintentos.
   - Inactivación y suspensión de socios sin pérdida de historial (R-DOM-05).

4. `tests/test_medidores.py`:
   - Alta de medidor con número de serie único y lectura inicial.
   - Asignación de medidor a socio: medidor pasa a estado `INSTALADO`.
   - **Exclusividad (R-DOM-03):** Intento de asignar el mismo medidor a un segundo socio activo es rechazado de inmediato.
   - **Multi-medidor (R-DOM-02):** Un socio puede tener 2 o más medidores asignados simultáneamente.
   - **Retiro de Medidor (R-DOM-04):** Desasignación con lectura de retiro válida y rechazo si la lectura es inferior a la de instalación.
   - Historial de asignaciones preservado íntegramente.

