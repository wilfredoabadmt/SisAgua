# Plan de Implementación: Fase 5 - Transcripción Histórica y Regularización (005-transcripcion-historica-regularizacion)

## 1. Verificación Constitucional Previa (Constitution Check)

| Principio / Regla | Estado | Mecanismo de Garantía |
|---|---|---|
| **P1. Fidelidad de Negocio** | Cumple | Reglas extraídas textualmente de la Sección 8 de la fuente funcional. |
| **P2. Fuente Única de Verdad** | Cumple | Desglose honesto entre lecturas informativas y obligaciones económicas confirmadas. |
| **P3. Integridad Financiera** | Cumple | La regularización a `Obligacion` se ejecuta en transacción atómica. |
| **P4. Idempotencia** | Cumple | Bloqueo de duplicados por constraint `unique_obligacion_socio_servicio_periodo`. |
| **P5. Conservación Histórica** | Cumple | Prohibición absoluta de `DELETE` físico en lotes y transcripciones. Se usa estado `RECHAZADO`. |
| **P6. Auditoría Verificable** | Cumple | Registro inmutable de transcriptor, validador, fechas y justificaciones en `BitacoraAuditoria`. |
| **P7. Seguridad por Defecto** | Cumple | Control RBAC con permisos `TRANSCRIPCION:VER`, `TRANSCRIPCION:CREAR`, `TRANSCRIPCION:VALIDAR`. |
| **P8. Transparencia Financiera** | Cumple | Separación explícita entre importe documentado en cuaderno e importe tarifario calculado. |
| **P10. Validación Previa** | Cumple | Una lectura histórica transcrita jamás devenga deuda sin validación y regularización explícita. |
| **R-DOM-18. Desacoplamiento** | Cumple | Las transcripciones no alteran el saldo del socio hasta su regularización. |
| **R-DOM-19. Regularización Trazable**| Cumple | Exige respaldo documentado, autorización y vínculo foreign key directo. |

---

## 2. Fases de Ejecución

### Fase 5.1: Modelos y Base de Datos
1. Crear la app `apps/transcripcion` y registrarla en `config/settings.py`.
2. Implementar los modelos `LoteTranscripcion` y `TranscripcionLectura` con protección `DELETE` P5.
3. Generar y aplicar migraciones (`makemigrations transcripcion`, `migrate`).

### Fase 5.2: Capa de Servicios de Negocio
1. Función `crear_lote_transcripcion(codigo, nombre, fuente, responsable, total_estimado)`.
2. Función `transcribir_lectura(lote, socio, medidor, periodo, lectura_anterior, lectura_actual, importe_documentado, foja, usuario)`.
3. Funciones de transición de estados: `validar_transcripcion()`, `observar_transcripcion()`, `rechazar_transcripcion()`.
4. Función `regularizar_deuda_historica(transcripcion, usuario_autorizador, motivo_respaldo, ip)` (R-DOM-19).
5. Función `calcular_avance_lote(lote)` (Sección 8.6).

### Fase 5.3: Pruebas Automatizadas (TDD)
1. Tests unitarios para ciclo de transcripción, monotonicidad histórica, cálculo de consumo e inmutabilidad P5 en `tests/test_transcripcion.py`.
2. Tests para regla R-DOM-18 (no deuda automática) y regla R-DOM-19 (regularización trazable a `Obligacion`) en `tests/test_regularizacion_deudas.py`.
3. Tests de vistas y reporte en `tests/test_transcripcion_views.py`.

### Fase 5.4: Interfaz de Usuario, Vistas y Exportación
1. Formularios en `apps/transcripcion/forms.py`.
2. Vistas en `apps/transcripcion/views.py`.
3. Plantillas en `templates/transcripcion/`:
   - `lotes_list.html`: Panel general y métricas de avance de digitalización.
   - `lote_detalle.html`: Detalle del lote, cuadro de avance y tabla de registros con filtros por estado.
   - `lote_form.html`: Alta de nuevo lote físico.
   - `captura_form.html`: Formulario de digitación de fila histórica.
   - `reporte_transcripcion.html`: Reporte imprimible y botón de descarga CSV.

### Fase 5.5: Navegación, Rutas y Certificación
1. Vincular rutas en `config/urls.py` y actualizar `fixtures/seed_menus.json`.
2. Ejecutar `pytest` y verificar 100% PASS en la suite completa de SisAgua.
3. Actualizar `CLAUDE.md`.

