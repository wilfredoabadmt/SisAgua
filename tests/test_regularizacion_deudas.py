import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.seguridad.models import Usuario
from apps.socios.models import Socio, Zona
from apps.servicios.models import Servicio, TipoServicio, ModalidadCobro, Obligacion, EstadoObligacion
from apps.transcripcion.models import LoteTranscripcion, EstadoTranscripcion
from apps.transcripcion.services import (
    crear_lote_transcripcion, transcribir_lectura,
    validar_transcripcion, regularizar_deuda_historica
)
from apps.caja.services import iniciar_turno_caja, procesar_cobro
from apps.caja.models import MetodoPago, EstadoRecibo
from apps.core.models import BitacoraAuditoria


@pytest.fixture
def servicio_agua_potable(db):
    return Servicio.objects.create(
        codigo="AGUA",
        nombre="Agua Potable",
        tipo_servicio=TipoServicio.AGUA_POTABLE,
        modalidad_cobro=ModalidadCobro.LECTURA_VOLUMETRICA
    )


@pytest.fixture
def socio_regularizacion(db):
    zona = Zona.objects.create(codigo="ZON-REG", nombre="Zona Regularización")
    return Socio.objects.create(
        codigo="SOC-REG-01",
        nombres="Mateo",
        apellidos="Vargas",
        ci="77665544",
        zona=zona
    )


@pytest.fixture
def lote_regularizacion(db, usuario_admin):
    return crear_lote_transcripcion(
        codigo="LOT-DEUDAS-2023",
        nombre="Cuaderno Deudas Antiguas 2023",
        fuente_documental="Libro de cuentas comunales 2023",
        responsable=usuario_admin,
        total_estimado=10
    )


@pytest.mark.django_db
def test_transcripcion_no_genera_deuda_automatica_r_dom_18(lote_regularizacion, socio_regularizacion, usuario_admin, servicio_agua_potable):
    """Regla R-DOM-18: Transcribir y validar una lectura histórica NO altera el estado de cuenta ni genera Obligacion."""
    registro = transcribir_lectura(
        lote=lote_regularizacion,
        socio=socio_regularizacion,
        periodo="2023-10",
        usuario=usuario_admin,
        lectura_anterior=Decimal('50.00'),
        lectura_actual=Decimal('70.00'),
        importe_documentado=Decimal('40.00')
    )
    validar_transcripcion(registro, usuario_admin)

    # Verificar que NO se haya creado ninguna Obligacion de cobro
    assert Obligacion.objects.filter(socio=socio_regularizacion).count() == 0

    # Saldo adeudado del socio debe continuar en 0.00
    deudas_socio = Obligacion.objects.filter(socio=socio_regularizacion, estado=EstadoObligacion.PENDIENTE)
    assert sum(d.saldo_pendiente for d in deudas_socio) == Decimal('0.00')


@pytest.mark.django_db
def test_regularizacion_deuda_historica_exitosa_r_dom_19(lote_regularizacion, socio_regularizacion, usuario_admin, servicio_agua_potable):
    """Regla R-DOM-19: La regularización formal crea una Obligacion económica exigible y auditable."""
    registro = transcribir_lectura(
        lote=lote_regularizacion,
        socio=socio_regularizacion,
        periodo="2023-11",
        usuario=usuario_admin,
        lectura_anterior=Decimal('70.00'),
        lectura_actual=Decimal('90.00'),
        importe_documentado=Decimal('50.00'),
        referencia_foja="Libro 2, Folio 15"
    )
    validar_transcripcion(registro, usuario_admin)

    motivo = "Aprobado por Asamblea General del Comité en Acta Nº 88 de fecha 10/01/2026."
    obligacion = regularizar_deuda_historica(
        transcripcion=registro,
        usuario_autorizador=usuario_admin,
        motivo_respaldo=motivo,
        ip_origen='192.168.1.100'
    )

    # Verificar creación de Obligacion
    assert obligacion.id is not None
    assert obligacion.socio == socio_regularizacion
    assert obligacion.monto == Decimal('50.00')
    assert obligacion.saldo_pendiente == Decimal('50.00')
    assert obligacion.estado == EstadoObligacion.PENDIENTE
    assert "Regularización Deuda Histórica 2023-11" in obligacion.concepto

    # Verificar actualización en el registro de transcripción
    registro.refresh_from_db()
    assert registro.estado == EstadoTranscripcion.MIGRADO
    assert registro.obligacion_regularizada == obligacion

    # Verificar auditoría P6
    audit = BitacoraAuditoria.objects.filter(
        modulo='TRANSCRIPCION',
        accion='REGULARIZAR_DEUDA_HISTORICA',
        registro_id=str(obligacion.id)
    ).first()
    assert audit is not None
    assert audit.usuario == usuario_admin


@pytest.mark.django_db
def test_deuda_regularizada_se_puede_cobrar_en_caja(lote_regularizacion, socio_regularizacion, usuario_admin, servicio_agua_potable):
    """Integración transaccional: una deuda histórica regularizada puede liquidarse en ventanilla de cobranzas."""
    registro = transcribir_lectura(
        lote=lote_regularizacion,
        socio=socio_regularizacion,
        periodo="2023-12",
        usuario=usuario_admin,
        importe_documentado=Decimal('60.00')
    )
    validar_transcripcion(registro, usuario_admin)
    obligacion = regularizar_deuda_historica(
        transcripcion=registro,
        usuario_autorizador=usuario_admin,
        motivo_respaldo="Reconocimiento expreso de deuda histórica firmado por el socio."
    )

    # Abrir turno de caja y cobrar la deuda regularizada
    turno = iniciar_turno_caja(usuario=usuario_admin, monto_apertura=Decimal('100.00'))
    recibo = procesar_cobro(
        turno=turno,
        socio=socio_regularizacion,
        obligaciones_ids=[obligacion.id],
        metodo_pago=MetodoPago.EFECTIVO,
        cajero=usuario_admin
    )

    assert recibo.estado == EstadoRecibo.EMITIDO
    assert recibo.monto_total == Decimal('60.00')
    obligacion.refresh_from_db()
    assert obligacion.estado == EstadoObligacion.PAGADA
    assert obligacion.saldo_pendiente == Decimal('0.00')


@pytest.mark.django_db
def test_regularizacion_falla_si_no_esta_validado(lote_regularizacion, socio_regularizacion, usuario_admin, servicio_agua_potable):
    """No se puede regularizar un registro que aún está en estado TRANSCRITO u OBSERVADO."""
    registro = transcribir_lectura(
        lote=lote_regularizacion,
        socio=socio_regularizacion,
        periodo="2023-01",
        usuario=usuario_admin,
        importe_documentado=Decimal('25.00')
    )
    # Sin validar
    with pytest.raises(ValidationError, match="Solo se pueden regularizar deudas con estado VALIDADO"):
        regularizar_deuda_historica(
            transcripcion=registro,
            usuario_autorizador=usuario_admin,
            motivo_respaldo="Aprobado en asamblea extraordinaria comunitaria."
        )


@pytest.mark.django_db
def test_regularizacion_impide_duplicacion_de_obligacion_p4(lote_regularizacion, socio_regularizacion, usuario_admin, servicio_agua_potable):
    """Idempotencia: si ya existe una obligación para ese periodo, se rechaza la duplicación."""
    # Crear obligación previa para 2023-02
    Obligacion.objects.create(
        socio=socio_regularizacion,
        servicio=servicio_agua_potable,
        periodo="2023-02",
        concepto="Consumo previo",
        monto=Decimal('30.00'),
        saldo_pendiente=Decimal('30.00'),
        fecha_emision=timezone.now().date(),
        fecha_vencimiento=timezone.now().date(),
        estado=EstadoObligacion.PENDIENTE
    )

    registro = transcribir_lectura(
        lote=lote_regularizacion,
        socio=socio_regularizacion,
        periodo="2023-02",
        usuario=usuario_admin,
        importe_documentado=Decimal('30.00')
    )
    validar_transcripcion(registro, usuario_admin)

    with pytest.raises(ValidationError, match="Ya existe una obligación económica registrada"):
        regularizar_deuda_historica(
            transcripcion=registro,
            usuario_autorizador=usuario_admin,
            motivo_respaldo="Intento de regularización duplicada sobre el mismo periodo."
        )

