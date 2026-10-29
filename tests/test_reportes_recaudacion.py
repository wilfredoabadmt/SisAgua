import pytest
from decimal import Decimal
from django.utils import timezone
from apps.socios.models import Socio, Zona, EstadoSocio
from apps.servicios.models import Servicio, TipoServicio, Obligacion, EstadoObligacion
from apps.caja.models import Recibo, EstadoRecibo, Pago, MetodoPago, DetalleRecibo, CajaTurno, EstadoTurnoCaja
from apps.reportes.services import (
    obtener_reporte_recaudacion,
    obtener_reporte_consumo,
    obtener_reporte_zonas,
    obtener_reporte_membresias,
    obtener_estado_cuenta_socio
)

@pytest.fixture
def datos_recaudacion(db, usuario_admin, usuario_cajero):
    zona = Zona.objects.create(codigo="Z-CENTRO", nombre="Zona Centro")
    socio = Socio.objects.create(
        codigo="SOC-100", nombres="Pedro", apellidos="Mamani",
        ci="4455667", zona=zona, estado=EstadoSocio.ACTIVO
    )
    serv_agua = Servicio.objects.create(codigo="AGUA", nombre="Consumo de Agua", tipo_servicio=TipoServicio.AGUA_POTABLE)
    serv_rep = Servicio.objects.create(codigo="REP", nombre="Reparación", tipo_servicio=TipoServicio.OTRO)

    obl1 = Obligacion.objects.create(
        socio=socio, servicio=serv_agua, periodo="2026-07",
        monto=Decimal('50.00'), saldo_pendiente=Decimal('0.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PAGADA
    )
    obl2 = Obligacion.objects.create(
        socio=socio, servicio=serv_agua, periodo="2026-08",
        monto=Decimal('30.00'), saldo_pendiente=Decimal('0.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PAGADA
    )
    obl3 = Obligacion.objects.create(
        socio=socio, servicio=serv_rep, periodo="2026-08",
        monto=Decimal('120.00'), saldo_pendiente=Decimal('0.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PAGADA
    )
    obl4 = Obligacion.objects.create(
        socio=socio, servicio=serv_agua, periodo="2026-09",
        monto=Decimal('60.00'), saldo_pendiente=Decimal('60.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PENDIENTE
    )

    turno = CajaTurno.objects.create(
        cajero=usuario_cajero,
        monto_apertura=Decimal('100.00'),
        estado=EstadoTurnoCaja.ABIERTA
    )

    # Recibo 1: Emitido Efectivo 50 Bs
    r1 = Recibo.objects.create(
        numero_recibo="REC-2026-000001", socio=socio, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('50.00'), monto_literal="Cincuenta 00/100 Bolivianos",
        codigo_verificacion="HASH001", metodo_pago=MetodoPago.EFECTIVO,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=r1, obligacion=obl1, concepto="Consumo de Agua", subtotal=Decimal('50.00'))

    # Recibo 2: Emitido QR 30 Bs
    r2 = Recibo.objects.create(
        numero_recibo="REC-2026-000002", socio=socio, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('30.00'), monto_literal="Treinta 00/100 Bolivianos",
        codigo_verificacion="HASH002", metodo_pago=MetodoPago.QR,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=r2, obligacion=obl2, concepto="Consumo de Agua", subtotal=Decimal('30.00'))

    # Recibo 3: Emitido Transferencia 120 Bs (Reparación)
    r3 = Recibo.objects.create(
        numero_recibo="REC-2026-000003", socio=socio, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('120.00'), monto_literal="Ciento veinte 00/100 Bolivianos",
        codigo_verificacion="HASH003", metodo_pago=MetodoPago.TRANSFERENCIA,
        estado=EstadoRecibo.EMITIDO
    )
    DetalleRecibo.objects.create(recibo=r3, obligacion=obl3, concepto="Reparación", subtotal=Decimal('120.00'))

    # Recibo 4: Anulado (60 Bs)
    r4 = Recibo.objects.create(
        numero_recibo="REC-2026-000004", socio=socio, cajero=usuario_cajero, turno=turno,
        monto_total=Decimal('60.00'), monto_literal="Sesenta 00/100 Bolivianos",
        codigo_verificacion="HASH004", metodo_pago=MetodoPago.EFECTIVO,
        estado=EstadoRecibo.ANULADO, motivo_anulacion="Error tipográfico en nombre",
        usuario_anulacion=usuario_admin, fecha_anulacion=timezone.now()
    )
    DetalleRecibo.objects.create(recibo=r4, obligacion=obl4, concepto="Consumo de Agua", subtotal=Decimal('60.00'))

    return {
        'socio': socio, 'zona': zona, 'turno': turno,
        'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4,
        'cajero': usuario_cajero, 'admin': usuario_admin
    }


def test_recaudacion_neta_discrimina_anulados_y_desglosa_medios_pago(datos_recaudacion):
    """
    Verifica que la recaudación neta contabilice exclusivamente recibos emitidos,
    desglose por efectivo, QR y transferencia, y reporte los anulados por separado.
    """
    rep = obtener_reporte_recaudacion()

    # Total neto = 50 + 30 + 120 = 200.00 (el anulado de 60 NO suma a caja neta)
    assert rep['total_neto'] == Decimal('200.00')
    assert rep['total_efectivo'] == Decimal('50.00')
    assert rep['total_qr'] == Decimal('30.00')
    assert rep['total_transferencia'] == Decimal('120.00')
    assert rep['cantidad_emitidos'] == 3

    # Anulados auditables
    assert rep['cantidad_anulados'] == 1
    assert rep['monto_anulado'] == Decimal('60.00')
    assert rep['recibos_anulados_lista'][0].numero_recibo == "REC-2026-000004"


def test_filtro_por_medio_de_pago_en_recaudacion(datos_recaudacion):
    """Verifica el filtro por medio de pago."""
    rep_qr = obtener_reporte_recaudacion(metodo_pago=MetodoPago.QR)
    assert rep_qr['total_neto'] == Decimal('30.00')
    assert rep_qr['cantidad_emitidos'] == 1

    rep_efectivo = obtener_reporte_recaudacion(metodo_pago=MetodoPago.EFECTIVO)
    assert rep_efectivo['total_neto'] == Decimal('50.00')


def test_estado_cuenta_socio_360(datos_recaudacion):
    """Verifica que el estado de cuenta individual del socio consolide medidores, facturas y recibos."""
    socio = datos_recaudacion['socio']
    serv_agua = Servicio.objects.get(codigo="AGUA")

    # Crear una obligación pendiente
    Obligacion.objects.create(
        socio=socio, servicio=serv_agua, periodo="2026-10",
        monto=Decimal('45.00'), saldo_pendiente=Decimal('45.00'),
        fecha_vencimiento=timezone.now().date(), estado=EstadoObligacion.PENDIENTE
    )

    res = obtener_estado_cuenta_socio(socio.id)
    assert res['socio'].id == socio.id
    assert res['total_facturado'] == Decimal('305.00')
    assert res['total_pendiente'] == Decimal('105.00')
    assert res['total_pagado'] == Decimal('200.00')
    assert len(res['recibos']) == 4
