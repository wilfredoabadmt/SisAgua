# Guía Rápida de Verificación: Fase 4 - Caja, Cobros, Recibos y Turnos (004-caja-cobros-recibos)

## 1. Requisitos Previos
Asegurarse de tener la base de datos sincronizada y fixtures cargadas:
```powershell
python manage.py migrate
python -m pytest tests/
```

---

## 2. Flujo de Prueba de Extremo a Extremo (E2E)

### Paso 1: Apertura de Turno de Caja
1. Iniciar sesión con un usuario que posea el rol `CAJERO` o `ADMINISTRADOR`.
2. Navegar a `/caja/turnos/apertura/`.
3. Ingresar un fondo de caja inicial, por ejemplo `100.00` Bs.
4. Presionar "Abrir Turno". Se confirmará la apertura exitosa y se habilitará la ventanilla de cobro.

### Paso 2: Búsqueda de Socio y Selección de Conceptos
1. Navegar a `/caja/cobros/`.
2. Buscar un socio por su código (ej. `SOC-0001`) o CI.
3. El sistema listará las obligaciones pendientes del socio (cuotas de agua, membresía, etc.).
4. Seleccionar una o varias obligaciones marcando las casillas correspondientes. El sistema actualizará el monto total no editable a cobrar.

### Paso 3: Confirmación y Emisión de Recibo
1. Seleccionar la forma de pago (Efectivo, QR o Transferencia).
2. Confirmar el cobro.
3. El sistema procesará atómicamente la transacción y redirigirá a `/caja/recibos/<id>/`.
4. Verificar la visualización del Recibo Oficial con:
   - Datos institucionales (Comité/Cooperativa).
   - Número de recibo correlativo único.
   - Datos del socio y cajero.
   - Detalle de ítems cobrados e importe total en números y literal boliviano.
   - Código QR de autenticidad.
   - Saldo remanente de la cuenta del socio.

### Paso 4: Anulación y Reversión (Supervisor)
1. Con un usuario administrador o supervisor (permiso `CAJA:ANULAR`), abrir el recibo emitido.
2. Hacer clic en "Anular Recibo".
3. Ingresar el motivo justificado de anulación (ej. "Error en método de pago a solicitud del socio").
4. Confirmar la anulación. Verificar que el recibo muestre la marca de agua `ANULADO` y que las obligaciones del socio hayan retornado al estado `PENDIENTE`.

### Paso 5: Arqueo y Cierre de Turno
1. Navegar a `/caja/turnos/cierre/`.
2. El sistema presentará el resumen de cobros por método y el total de efectivo esperado en gaveta.
3. Ingresar el importe físico declarado por el cajero.
4. Confirmar el cierre del turno. El turno pasará al estado `CERRADA` y se emitirá el resumen de arqueo.

