# Guía Rápida de Verificación: Fase 6 - Reportes Administrativos (006-reportes-administrativos-financieros)

## 1. Requisitos Previos
Asegurarse de tener la base de datos sincronizada:
```powershell
python manage.py migrate
python -m pytest tests/
```

---

## 2. Flujo de Prueba de Extremo a Extremo (E2E)

### Paso 1: Panel Ejecutivo de Reportes
1. Iniciar sesión con un usuario que posea el rol `ADMINISTRADOR`.
2. Navegar a `/reportes/`.
3. El sistema desplegará el panel central con los accesos directos y tarjetas de resumen ejecutivo.

### Paso 2: Reporte de Deudores
1. Navegar a `/reportes/deudores/`.
2. Filtrar por una zona específica o seleccionar "Solo deudas vencidas".
3. Verificar que la tabla despliegue:
   - Código, CI y nombre del socio.
   - Cantidad de medidores.
   - Deuda por agua y por membresía desagregada.
   - Antigüedad de la deuda en meses.
4. Presionar "Exportar a CSV" y verificar la descarga del archivo.
5. Presionar "Imprimir" y verificar el membrete institucional oficial en la vista preliminar.

### Paso 3: Reporte de Recaudación Financiera
1. Navegar a `/reportes/recaudacion/`.
2. Seleccionar el rango de fechas de hoy o del mes.
3. Verificar el cuadre entre total recaudado neto, cobros en efectivo y pagos digitales (QR/transferencia).
4. Si existen recibos anulados, verificar que se listen por separado sin contaminar el total cobrado neto.

### Paso 4: Estado de Cuenta Individual de Socio
1. Navegar a `/reportes/socio/<id>/` seleccionando un socio.
2. Comprobar que liste todas sus obligaciones históricas, los pagos aplicados, los recibos emitidos y el saldo remanente actual.

