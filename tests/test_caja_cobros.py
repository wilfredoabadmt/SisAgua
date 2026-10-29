import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.seguridad.models import Usuario, Rol
from apps.socios.models import Socio, Zona
from apps.servicios.models import Servicio, TipoServicio, ModalidadCobro, Obligacion, EstadoObligacion
from apps.caja.models import CajaTurno, EstadoTurnoCaja, Recibo, EstadoRecibo, Pago, MetodoPago
from apps.caja.services import iniciar_turno_caja, procesar_cobro, anular_recibo
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def zona_prueba(db):
    return Zona.objects.create(codigo="ZONA-NORTE", nombre="Zona Norte")


@pytest.fixture
def socio_prueba(db, zona_prueba):
    return Socio.objects.create(
        codigo="SOC-0010",
        nombres="Juan",
        apellidos="Perez",
        ci="4567890",
        zona=zona_prueba
    )


@pytest.fixture
def cajero_usuario(db, rol_cajero):
    return Usuario.objects.create_user(
        username="cajero1",
        password="Password123!",
        nombres="Pedro",
        apellido_paterno="Cajero",
        ci_numero="77889900",
        rol=rol_cajero,
        requiere_cambio_clave=False
    )


@pytest.fixture
def turno_abierto(db, cajero_usuario):
    return iniciar_turno_caja(
        usuario=cajero_usuario,
        monto_apertura=Decimal('50.00'),
        ip_origen='127.0.0.1'
    )


@pytest.fixture
def obligaciones_socio(db, socio_prueba):
    s_agua = Servicio.objects.create(
        codigo="AGUA",
        nombre="Agua Potable",
        tipo_servicio=TipoServicio.AGUA_POTABLE,
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )
    s_membresia = Servicio.objects.create(
        codigo="MEMBRESIA",
        nombre="Cuota de Afiliación",
        tipo_servicio=TipoServicio.MEMBRESIA,
        modalidad_cobro=ModalidadCobro.PAGO_UNICO_MEMBRESIA
    )
    
    o1 = Obligacion.objects.create(
        socio=socio_prueba,
        servicio=s_agua,
        periodo="2026-01",
        concepto="Consumo Agua Enero 2026",
        monto=Decimal('35.00'),
        saldo_pendiente=Decimal('35.00'),
        fecha_emision=timezone.now().date(),
        fecha_vencimiento=timezone.now().date(),
        estado=EstadoObligacion.PENDIENTE
    )
    o2 = Obligacion.objects.create(
        socio=socio_prueba,
        servicio=s_membresia,
        periodo="MEMBRESIA",
        concepto="Membresía Institucional",
        monto=Decimal('100.00'),
        saldo_pendiente=Decimal('100.00'),
        fecha_emision=timezone.now().date(),
        fecha_vencimiento=timezone.now().date(),
        estado=EstadoObligacion.PENDIENTE
    )
    return [o1, o2]


@pytest.mark.django_db
def test_cobro_multiconcepto_exitoso_y_emision_recibo_r_dom_16_r_dom_17(turno_abierto, socio_prueba, obligaciones_socio, cajero_usuario):
    """Prueba cobro multiconcepto atómico y emisión de recibo oficial correlativo."""
    o1, o2 = obligaciones_socio
    ids = [o1.id, o2.id]

    recibo = procesar_cobro(
        turno=turno_abierto,
        socio=socio_prueba,
        obligaciones_ids=ids,
        metodo_pago=MetodoPago.EFECTIVO,
        cajero=cajero_usuario,
        ip_origen='192.168.1.10'
    )

    assert recibo is not None
    assert recibo.estado == EstadoRecibo.EMITIDO
    assert recibo.numero_recibo.startswith("REC-")
    assert recibo.monto_total == Decimal('135.00')
    assert "CIENTO TREINTA Y CINCO 00/100 BOLIVIANOS" in recibo.monto_literal
    assert recibo.codigo_verificacion != ""
    assert recibo.detalles.count() == 2

    # Verificar liquidación 100% de obligaciones (R-DOM-15)
    o1.refresh_from_db()
    o2.refresh_from_db()
    assert o1.estado == EstadoObligacion.PAGADA
    assert o1.saldo_pendiente == Decimal('0.00')
    assert o2.estado == EstadoObligacion.PAGADA
    assert o2.saldo_pendiente == Decimal('0.00')

    # Verificar actualización acumuladores del turno
    turno_abierto.refresh_from_db()
    assert turno_abierto.total_efectivo_sistema == Decimal('135.00')
    assert turno_abierto.total_digital_sistema == Decimal('0.00')

    # Verificar auditoría
    audit = BitacoraAuditoria.objects.filter(
        modulo='CAJA',
        accion='COBRO_VENTANILLA',
        registro_id=str(recibo.id)
    ).first()
    assert audit is not None
    assert audit.usuario == cajero_usuario


@pytest.mark.django_db
def test_cobro_falla_si_obligacion_ya_fue_pagada_p4_idempotencia(turno_abierto, socio_prueba, obligaciones_socio, cajero_usuario):
    """Idempotencia: no se puede cobrar dos veces la misma obligación."""
    o1, _ = obligaciones_socio
    o1.estado = EstadoObligacion.PAGADA
    o1.saldo_pendiente = Decimal('0.00')
    o1.save()

    with pytest.raises(ValidationError, match="ya no está pendiente"):
        procesar_cobro(
            turno=turno_abierto,
            socio=socio_prueba,
            obligaciones_ids=[o1.id],
            metodo_pago=MetodoPago.EFECTIVO,
            cajero=cajero_usuario
        )


@pytest.mark.django_db
def test_cobro_bloqueado_si_turno_esta_cerrado(turno_abierto, socio_prueba, obligaciones_socio, cajero_usuario):
    """No se permite cobrar si el turno no está en estado ABIERTA."""
    turno_abierto.estado = EstadoTurnoCaja.CERRADA
    turno_abierto.save()

    o1 = obligaciones_socio[0]
    with pytest.raises(ValidationError, match="turno de caja cerrado"):
        procesar_cobro(
            turno=turno_abierto,
            socio=socio_prueba,
            obligaciones_ids=[o1.id],
            metodo_pago=MetodoPago.EFECTIVO,
            cajero=cajero_usuario
        )


@pytest.mark.django_db
def test_anulacion_autorizada_revierte_obligaciones_a_pendiente_r_dom_17_p5(turno_abierto, socio_prueba, obligaciones_socio, usuario_admin):
    """Anulación autorizada reabre las obligaciones a PENDIENTE y conserva el recibo (P5)."""
    o1, o2 = obligaciones_socio
    recibo = procesar_cobro(
        turno=turno_abierto,
        socio=socio_prueba,
        obligaciones_ids=[o1.id, o2.id],
        metodo_pago=MetodoPago.EFECTIVO,
        cajero=usuario_admin
    )

    # Anulación formal por supervisor
    motivo = "Cancelación por error en forma de pago a solicitud del socio titular."
    recibo_anulado = anular_recibo(
        recibo=recibo,
        usuario_supervisor=usuario_admin,
        motivo=motivo,
        ip_origen='10.0.0.5'
    )

    assert recibo_anulado.estado == EstadoRecibo.ANULADO
    assert recibo_anulado.usuario_anulacion == usuario_admin
    assert recibo_anulado.motivo_anulacion == motivo

    # Verificar reversión de obligaciones
    o1.refresh_from_db()
    o2.refresh_from_db()
    assert o1.estado == EstadoObligacion.PENDIENTE
    assert o1.saldo_pendiente == Decimal('35.00')
    assert o2.estado == EstadoObligacion.PENDIENTE
    assert o2.saldo_pendiente == Decimal('100.00')

    # Verificar ajuste en acumuladores de caja del turno abierto
    turno_abierto.refresh_from_db()
    assert turno_abierto.total_efectivo_sistema == Decimal('0.00')

    # Verificar auditoría
    audit = BitacoraAuditoria.objects.filter(
        modulo='CAJA',
        accion='ANULACION_RECIBO',
        registro_id=str(recibo.id)
    ).first()
    assert audit is not None


@pytest.mark.django_db
def test_anulacion_falla_sin_motivo_justificado(turno_abierto, socio_prueba, obligaciones_socio, usuario_admin):
    """La anulación exige justificación documentada (mínimo 10 caracteres)."""
    o1 = obligaciones_socio[0]
    recibo = procesar_cobro(
        turno=turno_abierto,
        socio=socio_prueba,
        obligaciones_ids=[o1.id],
        metodo_pago=MetodoPago.EFECTIVO,
        cajero=usuario_admin
    )

    with pytest.raises(ValidationError, match="justificación documentada"):
        anular_recibo(
            recibo=recibo,
            usuario_supervisor=usuario_admin,
            motivo="error"
        )


@pytest.mark.django_db
def test_bloqueo_de_borrado_fisico_en_recibo_y_pago_p5(turno_abierto, socio_prueba, obligaciones_socio, cajero_usuario):
    """Principio P5: Prohibido DELETE físico en recibos y pagos."""
    o1 = obligaciones_socio[0]
    recibo = procesar_cobro(
        turno=turno_abierto,
        socio=socio_prueba,
        obligaciones_ids=[o1.id],
        metodo_pago=MetodoPago.EFECTIVO,
        cajero=cajero_usuario
    )

    pago = recibo.pago

    with pytest.raises(ValidationError, match="No se permite eliminar físicamente un recibo"):
        recibo.delete()

    with pytest.raises(ValidationError, match="No se permite eliminar físicamente un registro de pago"):
        pago.delete()
