# Plan de Implementación: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 1 — Planificación y Constitution Check  
> **Fecha:** Octubre 2026  
> **Estado:** APROBADO  

---

## 1. Constitution Check (Puerta Constitucional Obligatoria)

| Regla / Principio | Criterio de Validación | Estado |
|---|---|:---:|
| **P1: Fidelidad de Negocio** | El cálculo mensual utiliza exclusivamente la tarifa vigente resuelta por `resolver_tarifa_vigente()`. | **PASS** |
| **P2: Fuente Única de Verdad** | La lectura anterior se obtiene de la última lectura válida o la lectura de instalación del medidor. | **PASS** |
| **P3: Integridad Financiera** | La generación de obligaciones del periodo se ejecuta en transacciones atómicas `transaction.atomic()`. | **PASS** |
| **P4: Idempotencia** | La facturación mensual no duplica deudas ante ejecuciones repetidas (`UniqueConstraint` sobre `socio, servicio, periodo`). | **PASS** |
| **P5: Conservación Histórica** | Cero `DELETE`. Correcciones guardan valor anterior, nuevo y motivo en `BitacoraAuditoria`. | **PASS** |
| **P6: Auditoría Verificable** | Toda lectura, observación, corrección y liquidación se audita con usuario e IP. | **PASS** |
| **P10: Validación Previa** | Lecturas en estado `OBSERVADA` o `ANULADA` son excluidas del queryset de facturación. | **PASS** |
| **R-DOM-06: Fórmula Consumo** | Consumo calculado como $\text{Lectura Actual} - \text{Lectura Anterior Válida}$. | **PASS** |
| **R-DOM-07: Monotonicidad** | Si $\text{Lectura Actual} < \text{Lectura Anterior}$, se clasifica inmediatamente como `OBSERVADA`. | **PASS** |
| **R-DOM-08: Unicidad Definitiva** | `UniqueConstraint(fields=['medidor', 'periodo'], condition=Q(activo=True))` a nivel de base de datos. | **PASS** |
| **R-DOM-09: Proforma** | Contiene leyenda visible: *"DOCUMENTO INFORMATIVO DE MEDICIÓN — NO CONSTITUYE RECIBO DE PAGO"*. | **PASS** |
| **R-DOM-10: No Retroactividad** | Tarifarios vigentes en la fecha del periodo son inmutables sobre deudas pasadas. | **PASS** |
| **R-DOM-11: Snapshot** | Cada obligación almacena en su concepto y detalle la copia congelada de los cálculos aplicados. | **PASS** |
| **R-DOM-12: Unicidad Mensual** | Una única obligación de agua por medidor y periodo mensual. | **PASS** |
| **R-DOM-14: Vencimiento** | Fecha calculada con el día configurado por la institución o fin de mes. | **PASS** |

**Resultado del Constitution Check:** **CONFORME (100% PASS). Aprobado para descomposición en tareas e implementación.**

---

## 2. Estructura del Módulo `apps/consumo`

```
apps/
└── consumo/
    ├── __init__.py
    ├── apps.py
    ├── models.py        # Lectura, EstadoLectura
    ├── forms.py         # CapturaLecturaForm, CorregirLecturaForm, FacturacionBatchForm
    ├── services.py      # resolver_lectura_anterior, registrar_lectura, corregir_lectura, facturar_periodo
    ├── views.py         # lecturas_list, captura_view, observadas_list, proforma_view, facturacion_view
    ├── urls.py
    └── templates/consumo/
        ├── lecturas_list.html
        ├── captura_form.html
        ├── observadas_list.html
        ├── corregir_form.html
        ├── proforma_detalle.html
        └── facturacion_panel.html
```

---

## 3. Estrategia de Testing (TDD)

Se desarrollará una suite en `tests/test_consumo_lecturas.py` y `tests/test_facturacion_agua.py` cubriendo:
1. `test_captura_lectura_valida_calcula_consumo_r_dom_06`.
2. `test_lectura_menor_a_anterior_dispara_observada_r_dom_07`.
3. `test_bloqueo_lectura_duplicada_mismo_periodo_r_dom_08`.
4. `test_correccion_lectura_observada_con_auditoria_p5_p6`.
5. `test_proforma_muestra_historial_real_sin_inventar_r_dom_09`.
6. `test_motor_facturacion_emite_obligaciones_con_tarifa_vigente_r_dom_10_r_dom_11`.
7. `test_motor_facturacion_excluye_lecturas_observadas_p10`.
8. `test_motor_facturacion_es_estrictamente_idempotente_r_dom_12`.
9. `test_calculo_vencimiento_fin_de_mes_r_dom_14`.

