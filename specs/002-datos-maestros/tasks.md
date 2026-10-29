# Lista de Tareas de Implementación: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 2 — Tareas Descompuestas y TDD  
> **Fecha:** Octubre 2026  
> **Estado:** COMPLETADO AL 100% (47/47 Tests PASS)  

---

## Fase 1: Creación de Módulos y Modelos de Dominio

- [x] **T001**: Crear aplicaciones Django `apps/socios`, `apps/servicios` y `apps/medidores`, y registrarlas en `INSTALLED_APPS` de `config/settings.py`.
- [x] **T002**: Implementar modelos en `apps/socios/models.py` (`Zona`, `Socio`, `EstadoSocio`) con `BaseAuditableModel`, unicidad compuesta `(ci, ci_complemento)` y método `delete()` protegido.
- [x] **T003**: Implementar modelos en `apps/servicios/models.py` (`Servicio`, `ModalidadCobro`, `Tarifario`, `TramoTarifario`, `Obligacion`, `EstadoObligacion`) con tipos monetarios exactos `DECIMAL(12,2)`.
- [x] **T004**: Implementar modelos en `apps/medidores/models.py` (`Medidor`, `EstadoMedidor`, `AsignacionMedidor`) con `UniqueConstraint(fields=['medidor'], condition=Q(activo=True))` para exclusividad (R-DOM-03).
- [x] **T005**: Generar y aplicar migraciones de base de datos para `socios`, `servicios` y `medidores`.

---

## Fase 2: Servicios de Dominio, Formularios y Tests (TDD)

- [x] **T006**: Escribir pruebas unitarias en `tests/test_zonas.py` (creación, unicidad de código, bloqueo de borrado físico, RBAC).
- [x] **T007**: Implementar formularios y vistas de Zonas en `apps/socios/` con plantillas HTML responsivas y auditoría automática.
- [x] **T008**: Escribir pruebas unitarias en `tests/test_servicios_tarifas.py` (catálogo, modalidades de cobro, resolución de tarifa vigente, no retroactividad R-DOM-10).
- [x] **T009**: Implementar formularios, servicios y vistas de Servicios y Tarifarios en `apps/servicios/` con plantillas HTML.
- [x] **T010**: Implementar servicio de dominio `registrar_socio()` en `apps/socios/services.py` con transacción atómica `transaction.atomic()` que crea al socio y emite la obligación de membresía única (R-DOM-13).
- [x] **T011**: Escribir pruebas unitarias en `tests/test_socios.py` validando CI único, generación correlativa de código, atomicidad de membresía e inmutabilidad de deudas (R-DOM-05).
- [x] **T012**: Implementar formularios y vistas de Socios (`SocioListView`, `SocioCreateView`, `SocioDetailView`, `SocioUpdateView`) y ficha integral 360° en `apps/socios/`.
- [x] **T013**: Implementar servicios de dominio `asignar_medidor()` y `desasignar_medidor()` en `apps/medidores/services.py` asegurando exclusividad y registro de lecturas.
- [x] **T014**: Escribir pruebas unitarias en `tests/test_medidores.py` validando exclusividad (R-DOM-03), multi-medición (R-DOM-02) y desasignación con lectura de retiro (R-DOM-04).
- [x] **T015**: Implementar formularios y vistas de Medidores (`MedidorListView`, `MedidorCreateView`, `AsignarMedidorView`, `RetirarMedidorView`) en `apps/medidores/`.

---

## Fase 3: RBAC, Menús de Navegación y Fixtures Canónicas

- [x] **T016**: Actualizar permisos RBAC en `fixtures/seed_roles_permisos.json` y menús dinámicos en `fixtures/seed_menus.json` para dar acceso a Zonas, Socios, Servicios, Medidores y Tarifario.
- [x] **T017**: Crear fixture `fixtures/seed_datos_maestros.json` con datos iniciales (Zonas, Servicios de Agua y Membresía, Tarifario Base).

---

## Fase 4: Verificación Integral E2E y Certificación

- [x] **T018**: Ejecutar suite completa con `python -m pytest tests/` y verificar 100% PASS (47/47 pruebas aprobadas).
- [x] **T019**: Actualizar `CLAUDE.md` documentando la finalización y certificación de la Fase 2.
