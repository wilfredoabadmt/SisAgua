import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from apps.seguridad.models import Usuario, Rol, Permiso
from apps.socios.models import Socio, Zona
from apps.servicios.models import Servicio, TipoServicio, ModalidadCobro, Obligacion, EstadoObligacion
from apps.transcripcion.models import LoteTranscripcion, EstadoLote, TranscripcionLectura, EstadoTranscripcion


@pytest.fixture
def servicio_agua_views(db):
    return Servicio.objects.create(
        codigo="AGUA-TRX",
        nombre="Agua Potable",
        tipo_servicio=TipoServicio.AGUA_POTABLE,
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )


@pytest.fixture
def zona_views(db):
    return Zona.objects.create(codigo="ZON-VIEW", nombre="Zona Views")


@pytest.fixture
def socio_views(db, zona_views):
    return Socio.objects.create(
        codigo="SOC-TRX-V1",
        nombres="Beatriz",
        apellidos="Castro",
        ci="99881122",
        zona=zona_views
    )


@pytest.fixture
def lote_views(db, usuario_admin):
    return LoteTranscripcion.objects.create(
        codigo="LOT-V1",
        nombre="Planilla 2024 Vistas",
        fuente_documental="Cuaderno 2024",
        responsable=usuario_admin,
        total_estimado=10
    )


@pytest.mark.django_db
def test_admin_accede_a_lotes_list(client, usuario_admin):
    client.force_login(usuario_admin)
    url = reverse('transcripcion:lotes_list')
    response = client.get(url)
    assert response.status_code == 200
    assert "Lotes de Transcripción y Migración Histórica" in response.content.decode('utf-8')


@pytest.mark.django_db
def test_usuario_sin_permiso_recibe_403(client, db):
    rol_vacio = Rol.objects.create(codigo="ROL_VACIO", nombre="Sin Permiso", es_sistema=False)
    user = Usuario.objects.create_user(
        username="sin_trx",
        password="Password123!",
        nombres="No",
        apellido_paterno="Access",
        ci_numero="99990000",
        rol=rol_vacio,
        requiere_cambio_clave=False
    )
    client.force_login(user)
    url = reverse('transcripcion:lotes_list')
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_flujo_completo_lote_captura_validacion_y_regularizacion_web(
    client, db, usuario_admin, socio_views, servicio_agua_views
):
    """Flujo end-to-end de transcripción y regularización vía HTTP."""
    client.force_login(usuario_admin)

    # 1. Crear lote
    url_lote_crear = reverse('transcripcion:lote_crear')
    resp_lote = client.post(url_lote_crear, {
        'codigo': 'LOT-E2E',
        'nombre': 'Planilla E2E 2023',
        'fuente_documental': 'Cuaderno original de campo',
        'periodo_predeterminado': '2023-05',
        'total_estimado': 15,
        'observaciones': 'Transcripción completa'
    })
    assert resp_lote.status_code == 302
    lote = LoteTranscripcion.objects.filter(codigo='LOT-E2E').first()
    assert lote is not None

    # 2. Capturar fila histórica
    url_captura = reverse('transcripcion:transcripcion_capturar', kwargs={'lote_id': lote.id})
    resp_captura = client.post(url_captura, {
        'socio': socio_views.id,
        'periodo': '2023-05',
        'lectura_anterior': '10.00',
        'lectura_actual': '25.00',
        'importe_documentado': '30.00',
        'referencia_foja': 'Libro 1, Foja 5',
        'observaciones': 'Sin observaciones'
    })
    assert resp_captura.status_code == 302
    registro = TranscripcionLectura.objects.filter(lote=lote, socio=socio_views).first()
    assert registro is not None
    assert registro.estado == EstadoTranscripcion.TRANSCRITO
    assert registro.consumo_calculado == Decimal('15.00')

    # 3. Validar registro por supervisor
    url_validar = reverse('transcripcion:transcripcion_validar', kwargs={'pk': registro.id})
    resp_val = client.post(url_validar)
    assert resp_val.status_code == 302
    registro.refresh_from_db()
    assert registro.estado == EstadoTranscripcion.VALIDADO
    assert registro.validado_por == usuario_admin

    # 4. Regularizar a Obligacion económica (R-DOM-19)
    url_reg = reverse('transcripcion:transcripcion_regularizar', kwargs={'pk': registro.id})
    resp_reg = client.post(url_reg, {
        'motivo_respaldo': 'Aprobado por Asamblea General del Comité en Acta Nº 12.'
    })
    assert resp_reg.status_code == 302
    registro.refresh_from_db()
    assert registro.estado == EstadoTranscripcion.MIGRADO
    assert registro.obligacion_regularizada is not None
    assert registro.obligacion_regularizada.monto == Decimal('30.00')

    # 5. Reporte en formato CSV
    url_reporte_csv = reverse('transcripcion:reporte_transcripcion') + "?format=csv"
    resp_csv = client.get(url_reporte_csv)
    assert resp_csv.status_code == 200
    assert resp_csv['Content-Type'] == 'text/csv; charset=utf-8'
    assert 'LOT-E2E' in resp_csv.content.decode('utf-8')

