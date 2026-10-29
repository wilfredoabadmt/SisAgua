import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.medidores.models import Medidor, AsignacionMedidor
from apps.reportes.services import obtener_reporte_deudores

@pytest.fixture
def datos_deudores(db):
    zona1 = Zona.objects.create(codigo="Z-NORTE", nombre="Zona Norte")
    zona2 = Zona.objects.create(codigo="Z-SUR", nombre="Zona Sur")

    socio1 = Socio.objects.create(
        codigo="SOC-001", nombres="Juan", apellidos="Perez",
        ci="1234567", zona=zona1,
        estado=EstadoSocio.ACTIVO
    )
    socio2 = Socio.objects.create(
        codigo="SOC-002", nombres="Maria", apellidos="Gomez",
        ci="2345678", zona=zona2,
        estado=EstadoSocio.ACTIVO
    )

    # Medidores
    m1 = Medidor.objects.create(codigo="MED-001", numero_serie="SERIE-001")
    AsignacionMedidor.objects.create(socio=socio1, medidor=m1, activo=True, lectura_instalacion=Decimal('0.00'))
    m2 = Medidor.objects.create(codigo="MED-002", numero_serie="SERIE-002")
    AsignacionMedidor.objects.create(socio=socio1, medidor=m2, activo=True, lectura_instalacion=Decimal('0.00'))

    # Servicios
    serv_agua = Servicio.objects.create(codigo="AGUA", nombre="Consumo Agua", tipo_servicio=TipoServicio.AGUA_POTABLE)
    serv_mem = Servicio.objects.create(codigo="MEM", nombre="Membresia Afiliacion", tipo_servicio=TipoServicio.MEMBRESIA)
    serv_otro = Servicio.objects.create(codigo="REP", nombre="Reparacion Conexión", tipo_servicio=TipoServicio.OTRO)

    hoy = timezone.now().date()
    vencido_hace_10d = hoy - timedelta(days=10)
    vencido_hace_40d = hoy - timedelta(days=40)
    vigente_en_15d = hoy + timedelta(days=15)

    # Socio 1: 3 deudas pendientes (Agua 2026-08 vencida, Agua 2026-09 vigente, Membresía vencida)
    Obligacion.objects.create(
        socio=socio1, servicio=serv_agua, periodo="2026-08",
        monto=Decimal('35.00'), saldo_pendiente=Decimal('35.00'),
        fecha_vencimiento=vencido_hace_40d, estado=EstadoObligacion.PENDIENTE
    )
    Obligacion.objects.create(
        socio=socio1, servicio=serv_agua, periodo="2026-09",
        monto=Decimal('40.00'), saldo_pendiente=Decimal('40.00'),
        fecha_vencimiento=vigente_en_15d, estado=EstadoObligacion.PENDIENTE
    )
    Obligacion.objects.create(
        socio=socio1, servicio=serv_mem, periodo="2026-08",
        monto=Decimal('100.00'), saldo_pendiente=Decimal('100.00'),
        fecha_vencimiento=vencido_hace_40d, estado=EstadoObligacion.PENDIENTE
    )
    # Obligación pagada (no debe sumar a deuda)
    Obligacion.objects.create(
        socio=socio1, servicio=serv_otro, periodo="2026-07",
        monto=Decimal('50.00'), saldo_pendiente=Decimal('0.00'),
        fecha_vencimiento=vencido_hace_40d, estado=EstadoObligacion.PAGADA
    )

    # Socio 2: 1 deuda pendiente de otro servicio
    Obligacion.objects.create(
        socio=socio2, servicio=serv_otro, periodo="2026-09",
        monto=Decimal('80.00'), saldo_pendiente=Decimal('80.00'),
        fecha_vencimiento=vencido_hace_10d, estado=EstadoObligacion.PENDIENTE
    )

    return {
        'zona1': zona1, 'zona2': zona2,
        'socio1': socio1, 'socio2': socio2
    }


def test_consolidacion_deudores_sin_duplicados_seccion_10_1(datos_deudores):
    """
    Verifica que el reporte agrupe por socio sin duplicar filas por tener múltiples obligaciones o medidores,
    desglosando correctamente agua, membresía y otros conceptos.
    """
    rep = obtener_reporte_deudores()

    assert rep['total_socios_deudores'] == 2
    assert rep['total_deuda_general'] == Decimal('255.00')  # (35 + 40 + 100) + 80
    assert rep['total_deuda_agua'] == Decimal('75.00')
    assert rep['total_deuda_membresia'] == Decimal('100.00')
    assert rep['total_deuda_vencida'] == Decimal('215.00')  # 35 + 100 + 80 (40 está vigente)

    # Socio 1 debe figurar primero (mayor deuda: 175.00)
    filas = rep['deudores']
    fila_socio1 = filas[0]
    assert fila_socio1['socio'].id == datos_deudores['socio1'].id
    assert fila_socio1['total_pendiente'] == Decimal('175.00')
    assert fila_socio1['deuda_agua'] == Decimal('75.00')
    assert fila_socio1['deuda_membresia'] == Decimal('100.00')
    assert fila_socio1['importe_vencido'] == Decimal('135.00')  # 35 + 100
    assert fila_socio1['cantidad_medidores'] == 2
    assert fila_socio1['antiguedad_meses'] == 2  # periodos 2026-08 y 2026-09


def test_filtro_por_zona_en_reporte_deudores(datos_deudores):
    """Verifica que el filtro por zona reduzca el universo a los socios de esa zona."""
    rep_zona1 = obtener_reporte_deudores(zona_id=datos_deudores['zona1'].id)
    assert rep_zona1['total_socios_deudores'] == 1
    assert rep_zona1['deudores'][0]['socio'].id == datos_deudores['socio1'].id
    assert rep_zona1['total_deuda_general'] == Decimal('175.00')

    rep_zona2 = obtener_reporte_deudores(zona_id=datos_deudores['zona2'].id)
    assert rep_zona2['total_socios_deudores'] == 1
    assert rep_zona2['deudores'][0]['socio'].id == datos_deudores['socio2'].id
    assert rep_zona2['total_deuda_general'] == Decimal('80.00')


def test_filtro_solo_vencidas_en_reporte_deudores(datos_deudores):
    """Verifica que el parámetro solo_vencidas ignore obligaciones vigentes no devengadas en mora."""
    rep_vencidas = obtener_reporte_deudores(solo_vencidas=True)
    # Socio 1 tiene 2 vencidas (35 + 100 = 135), socio 2 tiene 1 vencida (80)
    assert rep_vencidas['total_deuda_general'] == Decimal('215.00')
    for d in rep_vencidas['deudores']:
        assert d['total_pendiente'] == d['importe_vencido']
