import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.medidores.models import Medidor, AsignacionMedidor, EstadoMedidor
from apps.medidores.services import asignar_medidor, desasignar_medidor
from apps.socios.models import Zona, Socio
from apps.core.models import BitacoraAuditoria

@pytest.fixture
def socio_base(db):
    zona = Zona.objects.create(codigo="ZON-MED", nombre="Zona Medidores")
    return Socio.objects.create(
        codigo="SOC-M1",
        ci="112233",
        nombres="Roberto",
        apellidos="Gutiérrez",
        zona=zona,
        direccion="Calle 10"
    )

@pytest.fixture
def socio_secundario(db):
    zona = Zona.objects.get(codigo="ZON-MED")
    return Socio.objects.create(
        codigo="SOC-M2",
        ci="445566",
        nombres="Patricia",
        apellidos="Arias",
        zona=zona,
        direccion="Calle 20"
    )

@pytest.mark.django_db
def test_admin_puede_listar_medidores(client, usuario_admin):
    client.force_login(usuario_admin)
    Medidor.objects.create(codigo="MED-LIST", numero_serie="SN-100", lectura_inicial=Decimal('0.00'))
    res = client.get(reverse('medidores:medidores_list'))
    assert res.status_code == 200
    assert "SN-100" in res.content.decode()

@pytest.mark.django_db
def test_alta_medidor_con_serie_unica_y_auditoria(client, usuario_admin):
    client.force_login(usuario_admin)
    data = {
        'codigo': 'med-005',
        'numero_serie': 'sn-5555-bol',
        'marca': 'Elster',
        'modelo': 'V200',
        'diametro': '1/2"',
        'lectura_inicial': '0.00',
        'estado': EstadoMedidor.DISPONIBLE
    }
    res = client.post(reverse('medidores:medidor_crear'), data=data)
    assert res.status_code == 302
    
    medidor = Medidor.objects.get(numero_serie='SN-5555-BOL')
    assert medidor.codigo == 'MED-005'
    assert medidor.estado == EstadoMedidor.DISPONIBLE

    audit = BitacoraAuditoria.objects.filter(modulo='MEDIDORES', accion='CREAR').latest('fecha_hora_utc')
    assert audit.usuario == usuario_admin
    assert audit.resultado == 'EXITO'

@pytest.mark.django_db
def test_rechazo_numero_serie_duplicado(client, usuario_admin):
    client.force_login(usuario_admin)
    Medidor.objects.create(codigo="M-1", numero_serie="SN-DUP-1", lectura_inicial=Decimal('0.00'))
    
    data = {
        'codigo': 'M-2',
        'numero_serie': 'SN-DUP-1',
        'lectura_inicial': '0.00',
        'estado': EstadoMedidor.DISPONIBLE
    }
    res = client.post(reverse('medidores:medidor_crear'), data=data)
    assert res.status_code == 200
    assert Medidor.objects.filter(numero_serie="SN-DUP-1").count() == 1

@pytest.mark.django_db
def test_asignacion_exclusiva_medidor_a_socio_r_dom_03(socio_base, socio_secundario, usuario_admin):
    medidor = Medidor.objects.create(
        codigo="MED-EXCL",
        numero_serie="SN-EXCL-1",
        lectura_inicial=Decimal('0.00'),
        estado=EstadoMedidor.DISPONIBLE
    )

    # 1. Asignar exitosamente a socio_base
    asig = asignar_medidor(
        medidor=medidor,
        socio=socio_base,
        lectura_instalacion=Decimal('0.00'),
        usuario=usuario_admin
    )
    assert asig.activo is True
    medidor.refresh_from_db()
    assert medidor.estado == EstadoMedidor.INSTALADO

    # 2. Intento de asignar el mismo medidor activo a socio_secundario (Regla R-DOM-03)
    with pytest.raises(ValidationError) as exc:
        asignar_medidor(
            medidor=medidor,
            socio=socio_secundario,
            lectura_instalacion=Decimal('10.00'),
            usuario=usuario_admin
        )
    assert "ya se encuentra asignado a una conexión activa" in str(exc.value)

@pytest.mark.django_db
def test_multimedidor_por_socio_r_dom_02(socio_base, usuario_admin):
    m1 = Medidor.objects.create(codigo="MED-MULTI-1", numero_serie="SN-M1", lectura_inicial=Decimal('0.00'))
    m2 = Medidor.objects.create(codigo="MED-MULTI-2", numero_serie="SN-M2", lectura_inicial=Decimal('0.00'))

    # El socio socio_base puede tener múltiples medidores asignados simultáneamente
    asig1 = asignar_medidor(medidor=m1, socio=socio_base, lectura_instalacion=Decimal('0.00'), usuario=usuario_admin)
    asig2 = asignar_medidor(medidor=m2, socio=socio_base, lectura_instalacion=Decimal('5.00'), usuario=usuario_admin)

    assert socio_base.asignaciones_medidor.filter(activo=True).count() == 2

@pytest.mark.django_db
def test_desasignar_medidor_exige_lectura_valida_r_dom_04(socio_base, socio_secundario, usuario_admin):
    medidor = Medidor.objects.create(codigo="MED-RET", numero_serie="SN-RET-1", lectura_inicial=Decimal('100.00'))
    asig = asignar_medidor(medidor=medidor, socio=socio_base, lectura_instalacion=Decimal('100.00'), usuario=usuario_admin)

    # Intento de retiro con lectura menor a la de instalación: RECHAZADO (R-DOM-04)
    with pytest.raises(ValidationError) as exc:
        desasignar_medidor(
            asignacion=asig,
            lectura_retiro=Decimal('95.00'),
            usuario=usuario_admin
        )
    assert "no puede ser inferior a la de instalación" in str(exc.value)

    # Retiro con lectura válida
    desasignar_medidor(
        asignacion=asig,
        lectura_retiro=Decimal('185.50'),
        fecha_retiro=date(2026, 10, 28),
        motivo_retiro="Cambio por renovación",
        nuevo_estado=EstadoMedidor.DISPONIBLE,
        usuario=usuario_admin
    )

    asig.refresh_from_db()
    assert asig.activo is False
    assert asig.lectura_retiro == Decimal('185.50')

    medidor.refresh_from_db()
    assert medidor.estado == EstadoMedidor.DISPONIBLE

    # Ahora que fue retirado, el medidor puede reasignarse a socio_secundario
    nueva_asig = asignar_medidor(
        medidor=medidor,
        socio=socio_secundario,
        lectura_instalacion=Decimal('185.50'),
        usuario=usuario_admin
    )
    assert nueva_asig.activo is True
    assert AsignacionMedidor.objects.filter(medidor=medidor).count() == 2

