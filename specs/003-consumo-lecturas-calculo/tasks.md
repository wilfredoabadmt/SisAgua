# Lista de Tareas de Implementación: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 2 — Tareas Descompuestas y TDD  
> **Fecha:** Octubre 2026  
> **Estado:** COMPLETADO AL 100% (61/61 Tests PASS)  

---

## Fase 1: Creación de Módulo y Modelo de Datos

- [x] **T001**: Crear aplicación Django `apps/consumo` y registrarla en `INSTALLED_APPS` de `config/settings.py`.
- [x] **T002**: Implementar modelo `Lectura` y `EstadoLectura` en `apps/consumo/models.py` con `BaseAuditableModel`, validación de monotonicidad en `clean()`, constraint de unicidad condicional `unique_lectura_activa_por_medidor_periodo` (R-DOM-08) y método `delete()` protegido (P5).
- [x] **T003**: Generar y aplicar migraciones de base de datos para `apps/consumo/`.

---

## Fase 2: Servicios de Dominio, Formularios y Pruebas de Lecturas (TDD)

- [x] **T004**: Implementar servicios de dominio `resolver_lectura_anterior()`, `registrar_lectura()` y `corregir_lectura()` en `apps/consumo/services.py`.
- [x] **T005**: Escribir pruebas automáticas en `tests/test_consumo_lecturas.py` validando monotonicidad (R-DOM-07), estado observado, unicidad mensual (R-DOM-08) y trazabilidad de correcciones (P5, P6).
- [x] **T006**: Implementar formularios `CapturaLecturaForm` y `CorregirLecturaForm` en `apps/consumo/forms.py`.
- [x] **T007**: Implementar vistas de lecturas (`lecturas_list`, `lectura_capturar`, `lecturas_observadas_list`, `lectura_corregir`, `proforma_detalle`) en `apps/consumo/views.py`.
- [x] **T008**: Diseñar plantillas HTML responsivas en `templates/consumo/` (`lecturas_list.html`, `captura_form.html`, `observadas_list.html`, `corregir_form.html`, `proforma_detalle.html`).

---

## Fase 3: Motor de Facturación Idempotente y Cuentas por Cobrar

- [x] **T009**: Implementar servicio `facturar_periodo_agua()` en `apps/consumo/services.py` con transaccionalidad ACID, resolución tarifaria (R-DOM-10), snapshot de liquidación (R-DOM-11), exclusión de observadas (P10) e idempotencia estricta (R-DOM-12).
- [x] **T010**: Escribir pruebas automáticas en `tests/test_facturacion_agua.py` validando emisión de obligaciones, snapshot, no duplicación ante reintentos y cálculo determinístico de vencimiento (R-DOM-14).
- [x] **T011**: Implementar vista de panel y disparo de facturación en `apps/consumo/views.py` y template `facturacion_panel.html`.

---

## Fase 4: Enrutamiento, Menús de Navegación y Certificación E2E

- [x] **T012**: Enlazar `apps/consumo/urls.py` en `config/urls.py` y actualizar rutas de menús dinámicos en `fixtures/seed_menus.json`.
- [x] **T013**: Ejecutar suite completa con `python -m pytest tests/` y verificar 100% PASS (61/61 pruebas aprobadas).
- [x] **T014**: Actualizar `CLAUDE.md` certificando la Fase 3 y preparando la Fase 4 (Caja y Cobranzas).
