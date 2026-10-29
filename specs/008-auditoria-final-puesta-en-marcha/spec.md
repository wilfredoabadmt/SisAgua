# Especificación de Requisitos: Fase 8 - Auditoría Final, Pruebas Integrales y Puesta en Marcha (008-auditoria-final-puesta-en-marcha)

## 1. Declaración del Problema y Objetivos
Para certificar la entrega del Sistema de Administración, Consumo y Cobro de Agua Potable (**SisAgua**) bajo la Constitución SDD v1.0 y el marco normativo de la Ley N° 2066 y directrices de la AAPS, se requiere una fase final de certificación que valide:
1. **Auditoría e Integridad Cruzada Integral:** Verificación exhaustiva de todas las reglas contra duplicación y corrupción de saldos (Sección 13 de la fuente funcional).
2. **Sanitización y Cero Fuga de Secretos:** Comprobación rigurosa de que contraseñas, tokens y hashes no se almacenen en `BitacoraAuditoria` (Principio P6).
3. **Mecanismo Institucional de Copias de Seguridad (Backup & Restore):** Comando oficial de gestión para exportar la base de datos íntegra con metadatos de auditoría y verificar su restaurabilidad (Sección 15).
4. **Verificación de Seguridad y Robustez Global:** Comprobación de invariantes de monotonicidad, bloqueo pesimista de cobros concurrentes, idempotencia estricta en facturación y protección IDOR en el portal.

## 2. Marco Normativo y Reglas de Negocio (Sección 13 y 15)
- **R-INT-01 (No Duplicidad de Socios):** Bloqueo a nivel BD de duplicación de CI + complemento.
- **R-INT-02 (Exclusividad de Asignación):** Bloqueo a nivel BD de asignación concurrente de un medidor a dos socios.
- **R-INT-03 (Unicidad de Lectura Definitiva):** Bloqueo a nivel BD de más de una lectura activa por medidor y periodo.
- **R-INT-04 (Idempotencia de Facturación):** Bloqueo estricto de duplicación de obligaciones de agua en el mismo periodo.
- **R-INT-05 (Unicidad Atómica de Membresía):** Prohibición de emitir más de una membresía por socio.
- **R-INT-06 (Prohibición de Doble Cobro):** Bloqueo transaccional ante intento de pagar una obligación ya saldada.
- **R-INT-07 (Cero Borrado Físico):** Intercepción de `DELETE` en entidades maestras e históricas (Principio P5).
- **R-INT-08 (No Retroactividad Tarifaria):** Preservación de tarifas históricas inmutables sin aplicar tablas vigentes a periodos antiguos.
- **R-INT-09 (Respaldo Documentado de Deuda Histórica):** Prohibición de regularizar deudas sin validación de supervisor y folio físico.

## 3. Criterios de Aceptación (BDD)
1. **Comando de Verificación de Integridad:** Un comando administrativo `python manage.py verificar_integridad_sistema` ejecuta chequeos de salud sobre toda la base de datos y reporta discrepancias o certifica salud al 100%.
2. **Comando Institucional de Respaldo:** Un comando `python manage.py backup_institucional` genera un volcado JSON/SQL verificado con checksum SHA-256 e información de la institución.
3. **Suite Completa de Certificación E2E:** 100% de las pruebas automatizadas (abarcando las 8 fases) aprobadas sin errores.

