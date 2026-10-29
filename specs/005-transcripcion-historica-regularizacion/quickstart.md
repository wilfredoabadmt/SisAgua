# Guía Rápida de Verificación: Fase 5 - Transcripción Histórica y Regularización (005-transcripcion-historica-regularizacion)

## 1. Requisitos Previos
Asegurarse de tener la base de datos sincronizada:
```powershell
python manage.py migrate
python -m pytest tests/
```

---

## 2. Flujo de Prueba de Extremo a Extremo (E2E)

### Paso 1: Creación de un Lote de Transcripción
1. Iniciar sesión con un usuario que posea permiso `TRANSCRIPCION:CREAR`.
2. Navegar a `/transcripcion/lotes/crear/`.
3. Ingresar:
   - Código: `LOT-2024-NORTE`
   - Nombre: `Planilla de Lecturas 2024 - Sector Norte`
   - Fuente documental: `Cuaderno manuscrito empastado tomo 1`
   - Total estimado: `50` registros
4. Guardar. El sistema creará el lote en estado `ABIERTO`.

### Paso 2: Transcripción de Registro Histórico
1. Desde el detalle del lote, presionar "Transcribir Lectura".
2. Seleccionar socio (ej. `SOC-0001`), periodo `2024-06`, lectura anterior `100`, lectura actual `125`, e importe documentado `35.00` Bs.
3. Guardar. El registro quedará en estado `TRANSCRITO` con consumo calculado de 25 m³.
4. Verificar que en la ventanilla de cobranzas `/caja/cobros/` este registro **NO** figure como deuda exigible (Regla R-DOM-18).

### Paso 3: Validación por Supervisor
1. Con un usuario con permiso `TRANSCRIPCION:VALIDAR`, abrir el lote y revisar el registro.
2. Hacer clic en "Aprobar / Validar".
3. El estado del registro cambiará a `VALIDADO`, registrando al supervisor y la fecha exacta.

### Paso 4: Regularización de Deuda Histórica (R-DOM-19)
1. Presionar "Regularizar como Deuda".
2. Ingresar la justificación de respaldo: *"Aprobado por Asamblea General del Comité en fecha 15/01/2026"*.
3. Confirmar.
4. El registro pasará al estado `MIGRADO` con vínculo directo a la nueva `Obligacion` económica creada.
5. Ir a `/caja/cobros/?q=SOC-0001` y verificar que ahora sí aparece la obligación devengada de Bs 35.00 lista para cobro en ventanilla.

### Paso 5: Reporte de Avance de Migración
1. Navegar a `/transcripcion/reporte/`.
2. Verificar el cuadro de avance porcentual y las métricas por estado.
3. Probar la exportación a CSV.

