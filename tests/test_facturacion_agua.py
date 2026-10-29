import pytest
from decimal import Decimal
from datetime import date
from apps.socios.models import Zona, Socio
from apps.medidores.models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.servicios.models import Servicio, Tarifario, Obligacion, ModalidadCobro, EstadoObligacion
from apps.consumo.models import Lectura, EstadoLectura
from apps.consumo.services import registrar_lectura, facturar_periodo_agua
from apps.configuracion.models import Institucion

@pytest.fixture
def entorno_facturacion(db):
    institucion = Institucion.get_solo()
    institucion.dia_vencimiento_default = 15
    institucion.save()

    zona = Zona.objects.create(codigo="ZON-FAC", nombre="Zona Facturación")
    
    servicio_agua = Servicio.objects.create(
        codigo="AGUA",
        nombre="Agua Potable",
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )

    tarifario = Tarifario.objects.create(
        nombre="Tarifario Base 2026",
        servicio=servicio_agua,
        tarifa_basica=Decimal('10.00'),
        consumo_minimo_m3=Decimal('10.00'),
        precio_adicional_m3=Decimal('2.00'),
        fecha_vigencia_desde=date(2026, 1, 1)
    )

    # Socio 1 con Medidor 1
    s1 = Socio.objects.create(codigo="SOC-F1", ci="1001", nombres="Mario", apellidos="Rocha", zona=zona, direccion="Calle 1")
    m1 = Medidor.objects.create(codigo="MED-F1", numero_serie="SN-F1", lectura_inicial=Decimal('100.00'), estado=EstadoMedidor.INSTALADO)
    AsignacionMedidor.objects.create(medidor=m1, socio=s1, lectura_instalacion=Decimal('100.00'), activo=True)

    # Socio 2 con Medidor 2
    s2 = Socio.objects.create(codigo="SOC-F2", ci="1002", nombres="Elena", apellidos="Paz", zona=zona, direccion="Calle 2")
    m2 = Medidor.objects.create(codigo="MED-F2", numero_serie="SN-F2", lectura_inicial=Decimal('200.00'), estado=EstadoMedidor.INSTALADO)
    AsignacionMedidor.objects.create(medidor=m2, socio=s2, lectura_instalacion=Decimal('200.00'), activo=True)

    # Socio 3 con Medidor 3 (para prueba de lectura observada)
    s3 = Socio.objects.create(codigo="SOC-F3", ci="1003", nombres="Lucas", apellidos="Ríos", zona=zona, direccion="Calle 3")
    m3 = Medidor.objects.create(codigo="MED-F3", numero_serie="SN-F3", lectura_inicial=Decimal('300.00'), estado=EstadoMedidor.INSTALADO)
    AsignacionMedidor.objects.create(medidor=m3, socio=s3, lectura_instalacion=Decimal('300.00'), activo=True)

    return s1, s2, s3, m1, m2, m3, servicio_agua, tarifario

@pytest.mark.django_db
def test_facturacion_periodo_emite_obligaciones_correctamente(entorno_facturacion, usuario_admin):
    s1, s2, s3, m1, m2, m3, servicio_agua, _ = entorno_facturacion

    # Medidor 1: consumo 10 m³ (lectura 110.00) -> Bs 10.00 (mínimo)
    registrar_lectura(medidor=m1, periodo="2026-10", lectura_actual=Decimal('110.00'), usuario=usuario_admin)

    # Medidor 2: consumo 15 m³ (lectura 215.00) -> Bs 10.00 + (5 m³ * 2.00) = Bs 20.00
    registrar_lectura(medidor=m2, periodo="2026-10", lectura_actual=Decimal('215.00'), usuario=usuario_admin)

    # Medidor 3: lectura observada (actual 290 < 300)
    registrar_lectura(medidor=m3, periodo="2026-10", lectura_actual=Decimal('290.00'), usuario=usuario_admin)

    resumen = facturar_periodo_agua(periodo="2026-10", usuario=usuario_admin)

    assert resumen['obligaciones_generadas'] == 2
    assert resumen['lecturas_observadas_omitidas'] == 1
    assert resumen['monto_total_bs'] == Decimal('30.00')

    # Verificar que el vencimiento es en noviembre según R-DOM-14 (día 15)
    assert resumen['fecha_vencimiento'] == date(2026, 11, 15)

    # Verificar obligación generada para Socio 1
    ob1 = Obligacion.objects.get(socio=s1, periodo="2026-10")
    assert ob1.monto == Decimal('10.00')
    assert ob1.saldo_pendiente == Decimal('10.00')
    assert ob1.estado == EstadoObligacion.PENDIENTE

    # Verificar obligación generada para Socio 2
    ob2 = Obligacion.objects.get(socio=s2, periodo="2026-10")
    assert ob2.monto == Decimal('20.00')

    # Verificar que para Socio 3 NO se generó obligación (P10)
    assert not Obligacion.objects.filter(socio=s3, periodo="2026-10").exists()

@pytest.mark.django_db
def test_facturacion_es_estrictamente_idempotente_r_dom_12(entorno_facturacion, usuario_admin):
    s1, _, _, m1, _, _, _, _ = entorno_facturacion
    registrar_lectura(medidor=m1, periodo="2026-10", lectura_actual=Decimal('112.00'), usuario=usuario_admin)

    # 1era ejecución
    r1 = facturar_periodo_agua(periodo="2026-10", usuario=usuario_admin)
    assert r1['obligaciones_generadas'] == 1
    assert Obligacion.objects.filter(periodo="2026-10").count() == 1

    # 2da ejecución (reintento accidental o caída de red): IDEMPOTENCIA TOTAL
    r2 = facturar_periodo_agua(periodo="2026-10", usuario=usuario_admin)
    assert r2['obligaciones_generadas'] == 0
    assert r2['omitidos_idempotencia'] == 1
    assert Obligacion.objects.filter(periodo="2026-10").count() == 1

@pytest.mark.django_db
def test_calculo_vencimiento_febrero_fin_de_mes_r_dom_14(entorno_facturacion, usuario_admin):
    institucion = Institucion.get_solo()
    institucion.dia_vencimiento_default = 31  # Día 31
    institucion.save()

    s1, _, _, m1, _, _, _, _ = entorno_facturacion
    registrar_lectura(medidor=m1, periodo="2026-01", lectura_actual=Decimal('105.00'), usuario=usuario_admin)

    # Facturación de enero: el vencimiento cae en febrero
    resumen = facturar_periodo_agua(periodo="2026-01", usuario=usuario_admin)
    
    # R-DOM-14: En febrero no existe día 31 -> deterministicamente 28 de febrero de 2026
    assert resumen['fecha_vencimiento'] == date(2026, 2, 28)

