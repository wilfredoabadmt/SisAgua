import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from apps.seguridad.models import Usuario, Rol, Permiso
from apps.socios.models import Socio, Zona
from apps.servicios.models import Servicio, TipoServicio, ModalidadCobro, Obligacion, EstadoObligacion
from apps.caja.models import CajaTurno, EstadoTurnoCaja, Recibo, EstadoRecibo, MetodoPago
from apps.caja.services import iniciar_turno_caja


@pytest.fixture
def zona_views(db):
    return Zona.objects.create(codigo="ZON-VIEW", nombre="Zona Views")


@pytest.fixture
def socio_views(db, zona_views):
    return Socio.objects.create(
        codigo="SOC-VIEW-1",
        nombres="Maria",
        apellidos="Lopez",
        ci="33445566",
        zona=zona_views
    )


@pytest.fixture
def obligacion_views(db, socio_views):
    s = Servicio.objects.create(
        codigo="AGUA-VIEW",
        nombre="Agua Potable",
        tipo_servicio=TipoServicio.AGUA_POTABLE,
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )
    return Obligacion.objects.create(
        socio=socio_views,
        servicio=s,
        periodo="2026-03",
        concepto="Consumo Marzo",
        monto=Decimal('45.00'),
        saldo_pendiente=Decimal('45.00'),
        fecha_emision=timezone.now().date(),
        fecha_vencimiento=timezone.now().date(),
        estado=EstadoObligacion.PENDIENTE
    )


@pytest.fixture
def cajero_client(client, db, rol_cajero):
    user = Usuario.objects.create_user(
        username="cajero_web",
        password="Password123!",
        nombres="Cajero",
        apellido_paterno="Web",
        ci_numero="12345678",
        rol=rol_cajero,
        requiere_cambio_clave=False
    )
    client.force_login(user)
    return client, user


@pytest.mark.django_db
def test_cajero_accede_a_ventanilla_cobros(cajero_client):
    client, _ = cajero_client
    url = reverse('caja:cobros')
    response = client.get(url)
    assert response.status_code == 200
    assert "Ventanilla de Cobro en Caja" in response.content.decode('utf-8')


@pytest.mark.django_db
def test_usuario_sin_permiso_caja_recibe_403(client, db):
    rol_vacio = Rol.objects.create(codigo="ROL_VACIO", nombre="Sin Permisos", es_sistema=False)
    user_sin_permiso = Usuario.objects.create_user(
        username="sin_permiso",
        password="Password123!",
        nombres="Sin",
        apellido_paterno="Permiso",
        ci_numero="88887777",
        rol=rol_vacio,
        requiere_cambio_clave=False
    )
    client.force_login(user_sin_permiso)

    url = reverse('caja:cobros')
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_flujo_completo_apertura_cobro_anulacion_y_cierre_web(client, db, usuario_admin, socio_views, obligacion_views):
    """Flujo end-to-end completo vía peticiones HTTP con usuario administrador."""
    client.force_login(usuario_admin)

    # 1. Apertura de turno
    url_apertura = reverse('caja:turno_apertura')
    resp_apertura = client.post(url_apertura, {'monto_apertura': '100.00'})
    assert resp_apertura.status_code == 302
    turno = CajaTurno.objects.filter(cajero=usuario_admin, estado=EstadoTurnoCaja.ABIERTA).first()
    assert turno is not None
    assert turno.monto_apertura == Decimal('100.00')

    # 2. Buscar socio en ventanilla
    url_cobros = reverse('caja:cobros') + f"?q={socio_views.codigo}"
    resp_busqueda = client.get(url_cobros)
    assert resp_busqueda.status_code == 200
    assert socio_views.codigo in resp_busqueda.content.decode('utf-8')
    assert "Consumo Marzo" in resp_busqueda.content.decode('utf-8')

    # 3. Procesar cobro web
    url_procesar = reverse('caja:procesar_cobro')
    resp_cobro = client.post(url_procesar, {
        'socio_id': socio_views.id,
        'obligaciones_ids': [obligacion_views.id],
        'metodo_pago': MetodoPago.EFECTIVO,
        'referencia_transaccion': 'Recibo caja ventanilla'
    })
    assert resp_cobro.status_code == 302
    
    obligacion_views.refresh_from_db()
    assert obligacion_views.estado == EstadoObligacion.PAGADA
    assert obligacion_views.saldo_pendiente == Decimal('0.00')

    recibo = Recibo.objects.filter(socio=socio_views).first()
    assert recibo is not None
    assert recibo.estado == EstadoRecibo.EMITIDO
    assert recibo.monto_total == Decimal('45.00')

    # 4. Ver recibo detalle
    url_detalle = reverse('caja:recibo_detalle', kwargs={'pk': recibo.id})
    resp_detalle = client.get(url_detalle)
    assert resp_detalle.status_code == 200
    assert recibo.numero_recibo in resp_detalle.content.decode('utf-8')

    # 5. Anulación formal del recibo
    url_anular = reverse('caja:recibo_anular', kwargs={'pk': recibo.id})
    resp_anular = client.post(url_anular, {
        'motivo': 'Error de digitación justificado por supervisor de ventanilla.'
    })
    assert resp_anular.status_code == 302
    recibo.refresh_from_db()
    assert recibo.estado == EstadoRecibo.ANULADO
    obligacion_views.refresh_from_db()
    assert obligacion_views.estado == EstadoObligacion.PENDIENTE
    assert obligacion_views.saldo_pendiente == Decimal('45.00')

    # 6. Arqueo y cierre de turno
    url_cierre = reverse('caja:turno_cierre')
    resp_cierre = client.post(url_cierre, {
        'monto_declarado_efectivo': '100.00',
        'observaciones_cierre': ''
    })
    assert resp_cierre.status_code == 302
    turno.refresh_from_db()
    assert turno.estado == EstadoTurnoCaja.CERRADA
    assert turno.diferencia_efectivo == Decimal('0.00')

