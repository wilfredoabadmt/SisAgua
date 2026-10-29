# Guía Rápida y Verificación: 002-datos-maestros

> **Feature:** Datos Maestros (Zonas, Socios, Servicios, Medidores y Tarifario)  
> **Fase SDD:** Fase 1 — Quickstart y Manual de Verificación  
> **Fecha:** Octubre 2026  

---

## 1. Migraciones y Base de Datos

Para aplicar las migraciones de los módulos de Fase 2:

```powershell
python manage.py makemigrations socios servicios medidores
python manage.py migrate
```

---

## 2. Carga de Fixtures Iniciales de Datos Maestros

Para sembrar datos canónicos de prueba (Servicio de Agua, Servicio de Membresía, Tarifario Base, Zonas iniciales y Permisos RBAC):

```powershell
python manage.py loaddata fixtures/seed_datos_maestros.json
```

---

## 3. Ejecución de la Suite de Pruebas

Para ejecutar la suite completa de pruebas unitarias y de integración de Fase 2:

```powershell
# Ejecutar todas las pruebas del proyecto
python -m pytest tests/ -v

# Ejecutar únicamente las pruebas de Fase 2
python -m pytest tests/test_zonas.py tests/test_servicios_tarifas.py tests/test_socios.py tests/test_medidores.py -v
```

---

## 4. Verificación Manual en Interfaz Web

1. Iniciar el servidor local:
   ```powershell
   python manage.py runserver
   ```
2. Iniciar sesión como `admin` en `http://localhost:8000/login/`.
3. Navegar a:
   - `/zonas/`: Crear la zona `ZON-CENTRO` ("Zona Central").
   - `/servicios/`: Verificar el catálogo de servicios (Agua Potable con lectura volumétrica y Membresía con pago único).
   - `/servicios/tarifarios/`: Verificar el tarifario activo con tarifa básica de Bs 10.00 por 10 $m^3$ y tramos configurados.
   - `/medidores/`: Crear el medidor `MED-0001` con serie `SN-2026-001` y lectura inicial `0.00`.
   - `/socios/crear/`: Registrar un socio nuevo ("Juan Pérez", CI 4892019).
     - Verificar que se le asigna el código `SOC-0001`.
     - Verificar que en la ficha del socio aparece automáticamente la obligación de Membresía de Afiliación con saldo pendiente.
   - `/medidores/1/asignar/`: Asignar el medidor `MED-0001` a Juan Pérez.
     - Verificar que el medidor pasa a estado `INSTALADO`.
     - Intentar asignar el mismo medidor a otro socio: el sistema debe mostrar error impidiendo la asignación doble.

