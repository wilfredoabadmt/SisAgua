# Plan de Implementación: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## 1. Verificación Constitucional Previa (Constitution Check)

| Principio / Regla | Estado | Mecanismo de Garantía |
|---|---|---|
| **P1. Fidelidad de Negocio** | Cumple | Reglas extraídas textualmente de Secciones 2.4 y 9 de la fuente. |
| **P2. Fuente Única de Verdad** | Cumple | Totales de caja, saldos y deudas calculados dinámicamente de la BD. |
| **P3. Integridad Financiera** | Cumple | Bloque transaccional ACID con `select_for_update()` en todas las operaciones de cobro y anulación. |
| **P4. Idempotencia** | Cumple | Bloqueo pesimista evita cobros dobles concurrentes. |
| **P5. Conservación Histórica** | Cumple | Prohibición absoluta de sentencias `DELETE` físico en `Recibo`, `Pago`, `DetalleRecibo` y `CajaTurno`. |
| **P6. Auditoría Verificable** | Cumple | Integración con `BitacoraAuditoria` en cobros, aperturas, cierres y anulaciones. |
| **P7. Seguridad por Defecto** | Cumple | Decoradores server-side `@requiere_permiso` con `CAJA:VER`, `CAJA:CREAR`, `CAJA:CERRAR` y `CAJA:ANULAR`. |
| **P8. Transparencia Financiera** | Cumple | Distinción clara de saldo anterior, monto cobrado y saldo posterior. |
| **R-DOM-15. No Pagos Parciales** | Cumple | Selección de obligaciones completas; prohibición de amortización parcial. |
| **R-DOM-16. Cobro Multiconcepto**| Cumple | Liquidación de agua, membresía y cargos varios en una sola operación atómica. |
| **R-DOM-17. Recibo Inalterable** | Cumple | Correlativo único, código QR, inmutabilidad y anulación autorizada con reversión. |

---

## 2. Fases de Ejecución

### Fase 4.1: Estructura Base, Modelos y Migraciones
1. Crear la app `apps/caja` con sus configuraciones y registrarla en `config/settings.py`.
2. Definir los modelos `CajaTurno`, `Recibo`, `DetalleRecibo` y `Pago` con protección contra borrado físico.
3. Generar y aplicar migraciones de Django (`makemigrations caja`, `migrate`).

### Fase 4.2: Capa de Servicios de Negocio (Lógica Financiera Transaccional)
1. Función `iniciar_turno_caja(usuario, monto_apertura, ip)`: Validación de un solo turno abierto por cajero.
2. Función `cerrar_turno_caja(turno, monto_declarado, observaciones, cerrado_por, ip)`: Cálculo de arqueo por medio de pago y registro de diferencias.
3. Función `procesar_cobro(turno, socio, obligaciones_ids, metodo_pago, referencia, ip)`:
   - Bloqueo pesimista `select_for_update()`.
   - Validación R-DOM-15 (pago 100% de obligaciones seleccionadas).
   - Generación de correlativo inalterable e importe literal en bolivianos.
   - Creación de `Pago`, `Recibo`, `DetalleRecibo`, actualización de `Obligacion` a `PAGADA`.
   - Generación de código QR y hash de verificación.
   - Auditoría P6.
4. Función `anular_recibo(recibo, usuario, motivo, ip)`:
   - Validación de permiso supervisor.
   - Transacción atómica: paso a `ANULADO`, reversión de obligaciones a `PENDIENTE` y auditoría.

### Fase 4.3: Pruebas Automatizadas (TDD)
1. Tests unitarios y de integración para cobros, bloqueo concurrente, regla R-DOM-15, anulación de recibos y reversión en `tests/test_caja_cobros.py`.
2. Tests para ciclo de turnos, arqueo y diferencias en `tests/test_caja_turnos.py`.
3. Verificación de 100% PASS en suite completa de pytest.

### Fase 4.4: Interfaz de Usuario y Plantillas
1. Formulario y vista de búsqueda de socios y panel de cobranza (`templates/caja/cobros.html`).
2. Modal/pantalla de confirmación de cobro.
3. Vista de Recibo Oficial apto para impresión con logotipo institucional, QR y detalle desglosado (`templates/caja/recibo_detalle.html`).
4. Listado histórico de recibos emitidos y formulario de anulación autorizada (`templates/caja/recibos_list.html`).
5. Vista de apertura de turno (`templates/caja/turno_apertura.html`).
6. Vista de arqueo y cierre de turno con resumen de totales (`templates/caja/turno_cierre.html`).
7. Listado histórico de turnos (`templates/caja/turnos_list.html`).

### Fase 4.5: Rutas, Permisos y Navegación
1. Conectar rutas en `config/urls.py` (`apps.caja.urls`).
2. Actualizar `fixtures/seed_menus.json` y los permisos del sistema.
3. Ejecutar suite global y actualizar `CLAUDE.md`.

