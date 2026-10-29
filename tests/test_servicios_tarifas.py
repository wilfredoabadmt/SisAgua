import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.servicios.models import Servicio, Tarifario, TramoTarifario, Obligacion, ModalidadCobro, TipoServicio, CategoriaTarifa
from apps.servicios.services import resolver_tarifa_vigente, calcular_costo_consumo
from apps.socios.models import Zona, Socio

@pytest.mark.django_db
def test_admin_puede_listar_servicios(client, usuario_admin):
    client.force_login(usuario_admin)
    Servicio.objects.create(codigo="AGUA", nombre="Agua Potable", modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA)
    res = client.get(reverse('servicios:servicios_list'))
    assert res.status_code == 200
    assert "Agua Potable" in res.content.decode()

@pytest.mark.django_db
def test_usuario_sin_permiso_servicios_recibe_403(client, usuario_cajero):
    client.force_login(usuario_cajero)
    res = client.get(reverse('servicios:servicios_list'))
    assert res.status_code == 403

@pytest.mark.django_db
def test_crear_servicio_exitosamente_y_auditoria(client, usuario_admin):
    client.force_login(usuario_admin)
    data = {
        'codigo': 'alcantarillado',
        'nombre': 'Red de Alcantarillado Sanitario',
        'tipo_servicio': TipoServicio.ALCANTARILLADO,
        'modalidad_cobro': ModalidadCobro.CUOTA_FIJA_MENSUAL,
        'descripcion': 'Cuota fija mensual de alcantarillado'
    }
    res = client.post(reverse('servicios:servicio_crear'), data=data)
    assert res.status_code == 302
    
    servicio = Servicio.objects.get(codigo='ALCANTARILLADO')
    assert servicio.nombre == 'Red de Alcantarillado Sanitario'
    assert servicio.modalidad_cobro == ModalidadCobro.CUOTA_FIJA_MENSUAL

@pytest.mark.django_db
def test_rechazo_codigo_servicio_duplicado(client, usuario_admin):
    client.force_login(usuario_admin)
    Servicio.objects.create(codigo="BASURA", nombre="Recojo Basura", modalidad_cobro=ModalidadCobro.CUOTA_FIJA_MENSUAL)
    data = {
        'codigo': 'BASURA',
        'nombre': 'Otro Basura',
        'modalidad_cobro': ModalidadCobro.CUOTA_FIJA_MENSUAL
    }
    res = client.post(reverse('servicios:servicio_crear'), data=data)
    assert res.status_code == 200
    assert Servicio.objects.filter(codigo="BASURA").count() == 1

@pytest.mark.django_db
def test_resolver_tarifa_vigente_y_no_retroactividad(db):
    servicio = Servicio.objects.create(
        codigo="AGUA-TEST",
        nombre="Agua Test",
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )
    
    # Tarifa año 2025
    tarifa_2025 = Tarifario.objects.create(
        nombre="Tarifa 2025",
        servicio=servicio,
        categoria=CategoriaTarifa.DOMESTICO,
        tarifa_basica=Decimal('8.00'),
        consumo_minimo_m3=Decimal('10.00'),
        precio_adicional_m3=Decimal('1.50'),
        fecha_vigencia_desde=date(2025, 1, 1),
        fecha_vigencia_hasta=date(2025, 12, 31)
    )

    # Tarifa año 2026 en adelante
    tarifa_2026 = Tarifario.objects.create(
        nombre="Tarifa 2026",
        servicio=servicio,
        categoria=CategoriaTarifa.DOMESTICO,
        tarifa_basica=Decimal('10.00'),
        consumo_minimo_m3=Decimal('10.00'),
        precio_adicional_m3=Decimal('2.00'),
        fecha_vigencia_desde=date(2026, 1, 1),
        fecha_vigencia_hasta=None  # Vigente
    )

    # Consulta para fecha de 2025
    res_2025 = resolver_tarifa_vigente(servicio, CategoriaTarifa.DOMESTICO, fecha=date(2025, 6, 15))
    assert res_2025 == tarifa_2025
    assert res_2025.tarifa_basica == Decimal('8.00')

    # Consulta para fecha de 2026 (R-DOM-10: no retroactividad)
    res_2026 = resolver_tarifa_vigente(servicio, CategoriaTarifa.DOMESTICO, fecha=date(2026, 5, 20))
    assert res_2026 == tarifa_2026
    assert res_2026.tarifa_basica == Decimal('10.00')

@pytest.mark.django_db
def test_calculo_consumo_estandar_fronteras(db):
    servicio = Servicio.objects.create(codigo="AGUA-CALC", nombre="Agua", modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA)
    tarifa = Tarifario.objects.create(
        nombre="Tarifario Base",
        servicio=servicio,
        categoria=CategoriaTarifa.DOMESTICO,
        tarifa_basica=Decimal('10.00'),
        consumo_minimo_m3=Decimal('10.00'),
        precio_adicional_m3=Decimal('2.00'),
        fecha_vigencia_desde=date(2026, 1, 1)
    )

    # Frontera 0 m³: Tarifa básica de Bs 10.00
    calc_0 = calcular_costo_consumo(tarifa, Decimal('0.00'))
    assert calc_0['total'] == Decimal('10.00')

    # Frontera 10 m³ (consumo mínimo incluido): Bs 10.00
    calc_10 = calcular_costo_consumo(tarifa, Decimal('10.00'))
    assert calc_10['total'] == Decimal('10.00')

    # Excedente 12 m³ (2 m³ excedentes * Bs 2.00 = 4.00 + 10.00 = Bs 14.00)
    calc_12 = calcular_costo_consumo(tarifa, Decimal('12.00'))
    assert calc_12['total'] == Decimal('14.00')

    # Excedente 15 m³ (5 m³ * 2.00 = 10.00 + 10.00 = Bs 20.00)
    calc_15 = calcular_costo_consumo(tarifa, Decimal('15.00'))
    assert calc_15['total'] == Decimal('20.00')

@pytest.mark.django_db
def test_bloqueo_de_borrado_servicio_con_obligaciones(db):
    zona = Zona.objects.create(codigo="ZON-X", nombre="Zona X")
    socio = Socio.objects.create(codigo="SOC-X", ci="998877", nombres="A", apellidos="B", zona=zona, direccion="D")
    servicio = Servicio.objects.create(codigo="AGUA-PROT", nombre="Agua", modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA)
    
    Obligacion.objects.create(
        socio=socio,
        servicio=servicio,
        periodo="2026-10",
        concepto="Consumo de Agua",
        monto=Decimal('20.00'),
        saldo_pendiente=Decimal('20.00'),
        fecha_emision=date(2026, 10, 1),
        fecha_vencimiento=date(2026, 10, 15)
    )

    with pytest.raises(ValidationError) as exc:
        servicio.delete()
    assert "No se permite eliminar un servicio que tiene obligaciones" in str(exc.value)

