import pytest
from decimal import Decimal
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.socios.models import Zona, Socio, EstadoSocio
from apps.socios.services import registrar_socio, generar_codigo_socio
from apps.servicios.models import Servicio, Obligacion, ModalidadCobro, TipoServicio, EstadoObligacion
from apps.core.models import BitacoraAuditoria

@pytest.fixture
def zona_demo(db):
    return Zona.objects.create(codigo="CENTRO", nombre="Zona Central")

@pytest.fixture
def servicio_membresia(db):
    return Servicio.objects.create(
        codigo="MEMB",
        nombre="Derecho de Membresía",
        tipo_servicio=TipoServicio.MEMBRESIA,
        modalidad_cobro=ModalidadCobro.PAGO_UNICO_MEMBRESIA
    )

@pytest.mark.django_db
def test_alta_socio_genera_membresia_atomicamente_r_dom_13(zona_demo, servicio_membresia, usuario_admin):
    datos = {
        'ci': '5892019',
        'nombres': 'María Elena',
        'apellidos': 'Condori Flores',
        'zona': zona_demo,
        'direccion': 'Calle Sucre N° 12',
        'telefono': '78912345'
    }
    socio = registrar_socio(datos, usuario=usuario_admin)

    assert socio.codigo == 'SOC-0001'
    assert socio.ci == '5892019'
    assert socio.estado == EstadoSocio.ACTIVO

    # Verificación de la Regla R-DOM-13: Emisión atómica de membresía única
    obligaciones = Obligacion.objects.filter(socio=socio)
    assert obligaciones.count() == 1
    
    membresia = obligaciones.first()
    assert membresia.servicio == servicio_membresia
    assert membresia.estado == EstadoObligacion.PENDIENTE
    assert membresia.monto == Decimal('50.00')
    assert membresia.saldo_pendiente == Decimal('50.00')
    assert membresia.periodo == f"MEMB-{socio.codigo}"

    # Verificación de auditoría
    audit = BitacoraAuditoria.objects.filter(modulo='SOCIOS', accion='CREAR').latest('fecha_hora_utc')
    assert audit.usuario == usuario_admin
    assert audit.resultado == 'EXITO'

@pytest.mark.django_db
def test_rechazo_ci_duplicado(zona_demo, usuario_admin):
    datos = {
        'ci': '4455667',
        'nombres': 'Pedro',
        'apellidos': 'Gómez',
        'zona': zona_demo,
        'direccion': 'Calle A'
    }
    registrar_socio(datos, usuario=usuario_admin)

    # Intentar registrar otro socio con el mismo CI
    datos_duplicado = {
        'ci': '4455667',
        'nombres': 'Pedro Segundo',
        'apellidos': 'Gómez',
        'zona': zona_demo,
        'direccion': 'Calle B'
    }
    with pytest.raises(ValidationError) as exc:
        registrar_socio(datos_duplicado, usuario=usuario_admin)
    assert "Ya existe un socio registrado con el CI 4455667" in str(exc.value)

@pytest.mark.django_db
def test_soporte_complemento_ci_para_homonimos(zona_demo, usuario_admin):
    socio1 = registrar_socio({
        'ci': '3344556',
        'ci_complemento': '',
        'nombres': 'Carlos',
        'apellidos': 'Quispe',
        'zona': zona_demo,
        'direccion': 'Zona Alta'
    }, usuario=usuario_admin)

    socio2 = registrar_socio({
        'ci': '3344556',
        'ci_complemento': '1A',
        'nombres': 'Carlos',
        'apellidos': 'Quispe',
        'zona': zona_demo,
        'direccion': 'Zona Baja'
    }, usuario=usuario_admin)

    assert socio1.id != socio2.id
    assert socio1.ci_formateado == '3344556'
    assert socio2.ci_formateado == '3344556-1A'

@pytest.mark.django_db
def test_codigo_correlativo_autogenerado(zona_demo, usuario_admin):
    s1 = registrar_socio({'ci': '111', 'nombres': 'A', 'apellidos': 'B', 'zona': zona_demo, 'direccion': 'D'}, usuario=usuario_admin)
    s2 = registrar_socio({'ci': '222', 'nombres': 'C', 'apellidos': 'D', 'zona': zona_demo, 'direccion': 'E'}, usuario=usuario_admin)
    assert s1.codigo == 'SOC-0001'
    assert s2.codigo == 'SOC-0002'

@pytest.mark.django_db
def test_inactivacion_socio_conserva_deudas_historicas_r_dom_05(client, usuario_admin, zona_demo, servicio_membresia):
    client.force_login(usuario_admin)
    socio = registrar_socio({'ci': '778899', 'nombres': 'David', 'apellidos': 'Vargas', 'zona': zona_demo, 'direccion': 'Av 1'}, usuario=usuario_admin)
    
    # Inactivar socio
    res = client.post(reverse('socios:socio_cambiar_estado', kwargs={'pk': socio.pk}), data={
        'nuevo_estado': EstadoSocio.INACTIVO,
        'motivo': 'Suspensión temporal solicitada'
    })
    assert res.status_code == 302
    socio.refresh_from_db()
    assert socio.estado == EstadoSocio.INACTIVO

    # R-DOM-05: La obligación de membresía sigue existiendo con saldo pendiente
    obligaciones = Obligacion.objects.filter(socio=socio)
    assert obligaciones.count() == 1
    assert obligaciones.first().saldo_pendiente == Decimal('50.00')

@pytest.mark.django_db
def test_bloqueo_de_borrado_fisico_en_socio(zona_demo):
    socio = Socio.objects.create(
        codigo="SOC-NO-DEL",
        ci="999999",
        nombres="Intento",
        apellidos="Borrado",
        zona=zona_demo,
        direccion="Dir"
    )
    with pytest.raises(ValidationError) as exc:
        socio.delete()
    assert "No se permite eliminar físicamente un socio" in str(exc.value)

@pytest.mark.django_db
def test_vista_socio_detalle_360(client, usuario_admin, zona_demo, servicio_membresia):
    client.force_login(usuario_admin)
    socio = registrar_socio({'ci': '1234000', 'nombres': 'Ana', 'apellidos': 'Ríos', 'zona': zona_demo, 'direccion': 'Plaza'}, usuario=usuario_admin)
    
    res = client.get(reverse('socios:socio_detalle', kwargs={'pk': socio.pk}))
    assert res.status_code == 200
    contenido = res.content.decode()
    assert "Ana Ríos" in contenido
    assert socio.codigo in contenido
    assert "Derecho de Membresía" in contenido

