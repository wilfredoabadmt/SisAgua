# Guía Rápida y Verificación: 003-consumo-lecturas-calculo

> **Feature:** Consumo, Lecturas Mensuales, Proformas y Cálculo de Obligaciones  
> **Fase SDD:** Fase 1 — Quickstart y Manual de Verificación  
> **Fecha:** Octubre 2026  

---

## 1. Migraciones y Base de Datos

```powershell
python manage.py makemigrations consumo
python manage.py migrate
```

---

## 2. Ejecución de la Suite de Pruebas

```powershell
# Ejecutar todas las pruebas del proyecto
python -m pytest tests/ -v

# Ejecutar únicamente las pruebas de Fase 3
python -m pytest tests/test_consumo_lecturas.py tests/test_facturacion_agua.py -v
```

---

## 3. Verificación Manual en Interfaz Web

1. Iniciar el servidor local:
   ```powershell
   python manage.py runserver
   ```
2. Iniciar sesión como `admin` en `http://localhost:8000/login/`.
3. Navegar a `/consumo/lecturas/`:
   - Seleccionar el periodo actual `2026-10`.
   - Seleccionar un medidor asignado y capturar una lectura válida: verificar que el consumo se calcula al instante ($\text{Consumo} = \text{Lectura Actual} - \text{Lectura Anterior}$).
   - Intentar registrar una lectura menor a la anterior: el sistema debe guardarla automáticamente como `OBSERVADA` (R-DOM-07) y mostrar advertencia.
4. Navegar a `/consumo/observadas/`:
   - Verificar que aparece la lectura observada.
   - Acceder a "Corregir" y registrar el valor corregido con su motivo para volverla `CORREGIDA`.
5. Navegar a `/consumo/proformas/<id>/`:
   - Verificar la proforma informativa con la leyenda obligatoria *"DOCUMENTO INFORMATIVO DE MEDICIÓN — NO CONSTITUYE RECIBO DE PAGO"* (R-DOM-09).
6. Navegar a `/consumo/facturacion/`:
   - Ejecutar la facturación del periodo `2026-10`: verificar la emisión de la `Obligacion` de agua con su detalle de liquidación.
   - Ejecutar de nuevo la facturación del mismo periodo: verificar que el sistema no duplica ninguna obligación (R-DOM-12: Idempotencia).

