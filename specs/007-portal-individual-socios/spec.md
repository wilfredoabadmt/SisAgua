# Especificación de Requisitos: Fase 7 - Portal Individual de Socios (007-portal-individual-socios)

## 1. Declaración del Problema y Objetivos
En las comunidades y cooperativas de agua potable reguladas bajo la Ley N° 2066 y directrices de la AAPS, los socios requieren consultar periódicamente sus consumos históricos, lecturas registradas, obligaciones pendientes de pago, recibos oficiales cancelados y proformas informativas sin depender de visitas presenciales continuas a la oficina administrativa.
Asimismo, es indispensable garantizar el **aislamiento estricto de identidad (Principio P7, Regla R-DOM-01)**: ningún socio puede acceder a datos, deudas, recibos o medidores de otros socios, aun conociendo sus códigos o números de serie.

## 2. Marco Normativo y Reglas de Negocio
- **Sección 11 de la Fuente Funcional (`SISTEMA DE ADMINISTRACION.docx`):**
  - Acceso seguro mediante credenciales individuales (`username` y contraseña gestionada bajo Argon2id).
  - Consulta de datos personales y actualización controlada de datos de contacto (teléfono, correo electrónico).
  - Visualización del parque de medidores asignados (activos e históricos).
  - Consulta de lecturas mensuales y evolución volumétrica ($m^3$).
  - Consulta de obligaciones pendientes y discriminación de mora vencida.
  - Historial de recibos oficiales emitidos con detalle desglosado y visualización de QR de autenticidad.
  - Generación/descarga de la **Proforma Informativa de Medición (R-DOM-09)** con leyenda expresa de no-recibo.
  - Bloqueo absoluto de operaciones de caja, facturación o edición de lecturas desde el portal del socio.
- **Principio P7 (Autorización Server-Side y Menor Privilegio):**
  - Permiso `PORTAL:VER` asignado al rol `SOCIO`.
  - Las consultas en base de datos filtran forzosamente por el socio vinculado a la sesión autenticada (`request.user.perfil_socio`).

## 3. Criterios de Aceptación (BDD)
1. **Acceso Autónomo:** Un usuario con rol `SOCIO` vinculado a un registro de socio puede acceder a `/portal/` y visualizar su resumen 360°.
2. **Aislamiento Estricto:** Si un socio intenta acceder a la proforma o recibo de otro socio manipulando la URL (`/portal/recibo/<otro_id>/`), el servidor responde con 403 Forbidden o 404 Not Found.
3. **Consulta de Lecturas y Consumo:** El socio visualiza sus lecturas mensuales cronológicas con indicación de $m^3$ consumidos y estado de lectura.
4. **Consulta de Cuentas por Cobrar:** El socio visualiza sus obligaciones pendientes clasificadas por concepto (Agua, Membresía, Otros) y fecha de vencimiento.
5. **Historial de Pagos y Recibos:** El socio puede ver sus comprobantes de pago oficiales (`REC-YYYY-000001`) y descargar/imprimir la constancia oficial.
6. **Actualización de Perfil:** El socio puede actualizar su número de teléfono y correo electrónico, registrándose la modificación en auditoría. No puede alterar su CI, código o zona asignada.
7. **Bloqueo a No-Socios:** Un usuario administrativo sin ficha de socio que intente ingresar al portal recibe mensaje indicando que no cuenta con un perfil de socio asignado.

