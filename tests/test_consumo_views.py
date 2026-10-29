import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from apps.socios.models import Zona, Socio
from apps.medidores.models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.servicios.models import Servicio, Tarifario, ModalidadCobro, Obligacion
from apps.consumo.models import Lectura, EstadoLectura

@pytest.fixture
def base_consumo_views(db):
    zona = Zona.objects.create(codigo="ZON-VW", nombre="Zona Views")
    socio = Socio.objects.create(codigo="SOC-VW1", ci="990011", nombres="Walter", apellidos="Flores", zona=zona, direccion="Calle 5")
    medidor = Medidor.objects.create(codigo="MED-VW1", numero_serie="SN-VW-01", lectura_inicial=Decimal('50.00'), estado=EstadoMedidor.INSTALADO)
    AsignacionMedidor.objects.create(medidor=medidor, socio=socio, lectura_instalacion=Decimal('50.00'), activo=True)
    
    servicio = Servicio.objects.create(codigo="AGUA", nombre="Agua Potable", modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA)
    Tarifario.objects.create(
        nombre="Tarifario Views 2026",
        servicio=servicio,
        tarifa_basica=Decimal('10.00'),
        consumo_minimo_m3=Decimal('10.00'),
        precio_adicional_m3=Decimal('2.00'),
        fecha_vigencia_desde=date(2026, 1, 1)
    )
    return socio, medidor

@pytest.mark.django_db
def test_admin_accede_a_lecturas_list(client, usuario_admin):
    client.force_login(usuario_admin)
    res = client.get(reverse('consumo:lecturas_list'))
    assert res.status_code == 200
    assert "Registro de Lecturas Mensuales" in res.content.decode()

@pytest.mark.django_db
def test_usuario_sin_permiso_recibe_403(client, usuario_cajero):
    client.force_login(usuario_cajero)
    res = client.get(reverse('consumo:lecturas_list'))
    assert res.status_code == 403

@pytest.mark.django_db
def test_captura_lectura_valida_via_web(client, usuario_admin, base_consumo_views):
    client.force_login(usuario_admin)
    _, medidor = base_consumo_views

    data = {
        'periodo': '2026-10',
        'medidor': medidor.pk,
        'lectura_actual': '65.00',
        'fecha_lectura': '2026-10-28',
        'observaciones': 'Sin novedades'
    }
    res = client.post(reverse('consumo:lectura_capturar'), data=data)
    assert res.status_code == 302
    
    lectura = Lectura.objects.get(medidor=medidor, periodo='2026-10')
    assert lectura.consumo_m3 == Decimal('15.00')
    assert lectura.estado == EstadoLectura.VALIDADA

@pytest.mark.django_db
def test_captura_lectura_menor_via_web_dispara_observada(client, usuario_admin, base_consumo_views):
    client.force_login(usuario_admin)
    _, medidor = base_consumo_views

    data = {
        'periodo': '2026-10',
        'medidor': medidor.pk,
        'lectura_actual': '40.00',  # Menor a 50.00
        'fecha_lectura': '2026-10-28'
    }
    res = client.post(reverse('consumo:lectura_capturar'), data=data)
    assert res.status_code == 302
    assert "observadas" in res.url

    lectura = Lectura.objects.get(medidor=medidor, periodo='2026-10')
    assert lectura.estado == EstadoLectura.OBSERVADA

@pytest.mark.django_db
def test_facturacion_ejecutar_via_web(client, usuario_admin, base_consumo_views):
    client.force_login(usuario_admin)
    socio, medidor = base_consumo_views

    # Registrar lectura válida
    Lectura.objects.create(
        medidor=medidor,
        socio=socio,
        periodo='2026-10',
        lectura_anterior=Decimal('50.00'),
        lectura_actual=Decimal('62.00'),
        consumo_m3=Decimal('12.00'),
        estado=EstadoLectura.VALIDADA
    )

    res = client.post(reverse('consumo:facturacion_ejecutar'), data={'periodo': '2026-10'})
    assert res.status_code == 302

    # Verificar que se generó la obligación
    ob = Obligacion.objects.get(socio=socio, periodo='2026-10')
    assert ob.monto == Decimal('14.00')  # 10 base + 2 excedentes * 2.00

