import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.seguridad.models import Usuario
from apps.caja.models import CajaTurno, EstadoTurnoCaja, MetodoPago
from apps.caja.services import iniciar_turno_caja, cerrar_turno_caja, procesar_cobro
from apps.socios.models import Socio, Zona
from apps.servicios.models import Servicio, TipoServicio, ModalidadCobro, Obligacion, EstadoObligacion
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def cajero(db, rol_cajero):
    return Usuario.objects.create_user(
        username="cajero_turno",
        password="Password123!",
        nombres="Rosa",
        apellido_paterno="Caja",
        ci_numero="99887766",
        rol=rol_cajero,
        requiere_cambio_clave=False
    )


@pytest.mark.django_db
def test_apertura_turno_exitosa_y_auditoria(cajero):
    """Apertura formal de turno de caja y verificación de auditoría P6."""
    turno = iniciar_turno_caja(
        usuario=cajero,
        monto_apertura=Decimal('100.00'),
        ip_origen='192.168.1.50'
    )

    assert turno.id is not None
    assert turno.cajero == cajero
    assert turno.monto_apertura == Decimal('100.00')
    assert turno.estado == EstadoTurnoCaja.ABIERTA
    assert turno.fecha_cierre is None

    audit = BitacoraAuditoria.objects.filter(
        modulo='CAJA',
        accion='APERTURA_TURNO',
        registro_id=str(turno.id)
    ).first()
    assert audit is not None
    assert audit.usuario == cajero


@pytest.mark.django_db
def test_rechazo_segundo_turno_abierto_simultaneo(cajero):
    """Un cajero no puede abrir dos turnos simultáneos."""
    iniciar_turno_caja(usuario=cajero, monto_apertura=Decimal('50.00'))

    with pytest.raises(ValidationError, match="ya cuenta con un turno de caja abierto"):
        iniciar_turno_caja(usuario=cajero, monto_apertura=Decimal('20.00'))


@pytest.mark.django_db
def test_cierre_turno_con_arqueo_exacto(cajero):
    """Cierre de turno con arqueo coincidente (diferencia 0.00)."""
    turno = iniciar_turno_caja(usuario=cajero, monto_apertura=Decimal('100.00'))

    # Cerrar declarando exactamente los 100.00 de fondo
    turno_cerrado = cerrar_turno_caja(
        turno=turno,
        monto_declarado_efectivo=Decimal('100.00'),
        observaciones="",
        cerrado_por=cajero,
        ip_origen='127.0.0.1'
    )

    assert turno_cerrado.estado == EstadoTurnoCaja.CERRADA
    assert turno_cerrado.monto_declarado_efectivo == Decimal('100.00')
    assert turno_cerrado.diferencia_efectivo == Decimal('0.00')
    assert turno_cerrado.fecha_cierre is not None

    audit = BitacoraAuditoria.objects.filter(
        modulo='CAJA',
        accion='CIERRE_TURNO',
        registro_id=str(turno.id)
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_cierre_turno_con_diferencia_exige_justificacion(cajero):
    """Si el arqueo tiene diferencias, se exige justificación en observaciones."""
    turno = iniciar_turno_caja(usuario=cajero, monto_apertura=Decimal('100.00'))

    # Faltante de 10 Bs sin observaciones debe fallar
    with pytest.raises(ValidationError, match="Debe ingresar una justificación detallada"):
        cerrar_turno_caja(
            turno=turno,
            monto_declarado_efectivo=Decimal('90.00'),
            observaciones="",
            cerrado_por=cajero
        )

    # Con observaciones justificadas debe cerrar correctamente
    turno_cerrado = cerrar_turno_caja(
        turno=turno,
        monto_declarado_efectivo=Decimal('90.00'),
        observaciones="Faltante de 10 Bs por redondeo en cambio de monedas de 50 centavos.",
        cerrado_por=cajero
    )

    assert turno_cerrado.estado == EstadoTurnoCaja.CERRADA
    assert turno_cerrado.diferencia_efectivo == Decimal('-10.00')
    assert "Faltante de 10 Bs" in turno_cerrado.observaciones_cierre


@pytest.mark.django_db
def test_bloqueo_de_borrado_fisico_en_turno_p5(cajero):
    """Principio P5: Prohibido DELETE físico en turnos de caja."""
    turno = iniciar_turno_caja(usuario=cajero, monto_apertura=Decimal('50.00'))

    with pytest.raises(ValidationError, match="No se permite eliminar un turno de caja"):
        turno.delete()

