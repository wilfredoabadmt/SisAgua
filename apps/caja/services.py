from decimal import Decimal
from typing import List, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.services import registrar_auditoria
from apps.seguridad.models import Usuario
from apps.socios.models import Socio
from apps.servicios.models import Obligacion, EstadoObligacion
from apps.caja.models import CajaTurno, EstadoTurnoCaja, Recibo, EstadoRecibo, DetalleRecibo, Pago, MetodoPago
from apps.caja.utils import monto_a_literal, generar_codigo_verificacion


def iniciar_turno_caja(
    usuario: Usuario,
    monto_apertura: Decimal,
    ip_origen: Optional[str] = None
) -> CajaTurno:
    """
    Abre una sesión/turno de caja para un cajero con un fondo inicial para cambio.
    Sección 9.5 de la fuente.
    """
    if monto_apertura is None or monto_apertura < Decimal('0.00'):
        raise ValidationError("El monto de apertura no puede ser negativo.")

    # Validar que el usuario no tenga ya un turno abierto
    if CajaTurno.objects.filter(cajero=usuario, estado=EstadoTurnoCaja.ABIERTA).exists():
        raise ValidationError(f"El usuario '{usuario.username}' ya cuenta con un turno de caja abierto.")

    turno = CajaTurno.objects.create(
        cajero=usuario,
        monto_apertura=monto_apertura,
        estado=EstadoTurnoCaja.ABIERTA,
        fecha_apertura=timezone.now()
    )

    registrar_auditoria(
        modulo='CAJA',
        accion='APERTURA_TURNO',
        resultado="EXITO",
        usuario=usuario,
        entidad_afectada='CajaTurno',
        registro_id=str(turno.id),
        detalle={
            'turno_id': turno.id,
            'cajero': usuario.username,
            'monto_apertura': str(monto_apertura),
            'fecha_apertura': turno.fecha_apertura.isoformat()
        },
        ip_origen=ip_origen
    )

    return turno


def cerrar_turno_caja(
    turno: CajaTurno,
    monto_declarado_efectivo: Decimal,
    observaciones: str = '',
    cerrado_por: Optional[Usuario] = None,
    ip_origen: Optional[str] = None
) -> CajaTurno:
    """
    Realiza el arqueo físico y el cierre formal de un turno de caja.
    Sección 9.5 de la fuente.
    """
    if turno.estado != EstadoTurnoCaja.ABIERTA:
        raise ValidationError("El turno ya se encuentra cerrado.")

    if monto_declarado_efectivo is None or monto_declarado_efectivo < Decimal('0.00'):
        raise ValidationError("Debe ingresar un monto declarado válido y no negativo.")

    usuario_cierre = cerrado_por or turno.cajero

    with transaction.atomic():
        # Recalcular sumas reales desde los pagos del turno para máxima consistencia (P2, P3)
        pagos_turno = Pago.objects.filter(turno=turno, recibo__estado=EstadoRecibo.EMITIDO)
        total_efectivo = Decimal('0.00')
        total_digital = Decimal('0.00')

        for p in pagos_turno:
            if p.metodo_pago == MetodoPago.EFECTIVO:
                total_efectivo += p.monto
            else:
                total_digital += p.monto

        turno.total_efectivo_sistema = total_efectivo
        turno.total_digital_sistema = total_digital

        efectivo_esperado = turno.monto_apertura + total_efectivo
        diferencia = monto_declarado_efectivo - efectivo_esperado

        if diferencia != Decimal('0.00') and not observaciones.strip():
            raise ValidationError(
                f"Existe una diferencia de caja de Bs {diferencia}. "
                "Debe ingresar una justificación detallada en las observaciones."
            )

        turno.monto_declarado_efectivo = monto_declarado_efectivo
        turno.diferencia_efectivo = diferencia
        turno.observaciones_cierre = observaciones.strip()
        turno.fecha_cierre = timezone.now()
        turno.cerrado_por = usuario_cierre
        turno.estado = EstadoTurnoCaja.CERRADA
        turno.save()

    registrar_auditoria(
        modulo='CAJA',
        accion='CIERRE_TURNO',
        resultado="EXITO",
        usuario=usuario_cierre,
        entidad_afectada='CajaTurno',
        registro_id=str(turno.id),
        detalle={
            'turno_id': turno.id,
            'cajero': turno.cajero.username,
            'monto_apertura': str(turno.monto_apertura),
            'total_efectivo_sistema': str(total_efectivo),
            'total_digital_sistema': str(total_digital),
            'monto_declarado_efectivo': str(monto_declarado_efectivo),
            'diferencia_efectivo': str(diferencia),
            'observaciones': observaciones.strip(),
            'fecha_cierre': turno.fecha_cierre.isoformat()
        },
        ip_origen=ip_origen
    )

    return turno


def generar_siguiente_numero_recibo() -> str:
    """
    Genera un número de recibo oficial correlativo anual inalterable.
    Formato: REC-YYYY-000001
    """
    año_actual = timezone.now().year
    prefijo = f"REC-{año_actual}-"
    ultimo_recibo = Recibo.objects.filter(
        numero_recibo__startswith=prefijo
    ).order_by('-id').first()

    if ultimo_recibo:
        try:
            ultimo_correlativo = int(ultimo_recibo.numero_recibo.split('-')[-1])
            siguiente = ultimo_correlativo + 1
        except (ValueError, IndexError):
            siguiente = Recibo.objects.filter(numero_recibo__startswith=prefijo).count() + 1
    else:
        siguiente = 1

    return f"{prefijo}{siguiente:06d}"


def procesar_cobro(
    turno: CajaTurno,
    socio: Socio,
    obligaciones_ids: List[int],
    metodo_pago: str,
    referencia_transaccion: str = '',
    cajero: Optional[Usuario] = None,
    ip_origen: Optional[str] = None
) -> Recibo:
    """
    Ejecuta el cobro multiconcepto en ventanilla de forma estrictamente transaccional.
    Cumple P3 (Integridad), P4 (Idempotencia), R-DOM-15 (No pagos parciales),
    R-DOM-16 (Cobro multiconcepto) y R-DOM-17 (Recibo oficial correlativo).
    """
    if turno.estado != EstadoTurnoCaja.ABIERTA:
        raise ValidationError("No se puede registrar un cobro en un turno de caja cerrado.")

    usuario_cajero = cajero or turno.cajero

    if not obligaciones_ids:
        raise ValidationError("Debe seleccionar al menos una obligación para realizar el cobro.")

    with transaction.atomic():
        # Bloqueo concurrente pesimista (P3, R-DOM-16)
        obligaciones = list(
            Obligacion.objects.select_for_update().filter(
                id__in=obligaciones_ids,
                socio=socio
            )
        )

        if len(obligaciones) != len(set(obligaciones_ids)):
            raise ValidationError("Una o más obligaciones seleccionadas no existen o no pertenecen al socio.")

        # Verificar que todas estén pendientes
        for obl in obligaciones:
            if obl.estado != EstadoObligacion.PENDIENTE:
                raise ValidationError(
                    f"La obligación #{obl.id} ({obl.concepto}) ya no está pendiente (Estado: {obl.get_estado_display()})."
                )

        # Regla R-DOM-15: Prohibición de pagos parciales por obligación.
        # Cada obligación seleccionada se liquida por su saldo_pendiente total.
        monto_total_cobro = sum(obl.saldo_pendiente for obl in obligaciones)
        if monto_total_cobro <= Decimal('0.00'):
            raise ValidationError("El importe total de las obligaciones a cobrar debe ser mayor a cero.")

        # Calcular saldo previo y saldo posterior del socio
        saldo_anterior_socio = sum(
            o.saldo_pendiente for o in Obligacion.objects.filter(
                socio=socio,
                estado=EstadoObligacion.PENDIENTE
            )
        )
        saldo_posterior_socio = max(Decimal('0.00'), saldo_anterior_socio - monto_total_cobro)

        # Generar correlativo oficial inalterable
        numero_recibo = generar_siguiente_numero_recibo()
        monto_literal = monto_a_literal(monto_total_cobro)
        codigo_verificacion = generar_codigo_verificacion(numero_recibo, socio.codigo, monto_total_cobro)

        # Crear Recibo oficial
        recibo = Recibo.objects.create(
            numero_recibo=numero_recibo,
            socio=socio,
            turno=turno,
            cajero=usuario_cajero,
            fecha_emision=timezone.now(),
            metodo_pago=metodo_pago,
            monto_total=monto_total_cobro,
            monto_literal=monto_literal,
            saldo_anterior=saldo_anterior_socio,
            saldo_posterior=saldo_posterior_socio,
            codigo_verificacion=codigo_verificacion,
            estado=EstadoRecibo.EMITIDO
        )

        # Crear detalles del recibo y liquidar obligaciones al 100%
        for obl in obligaciones:
            DetalleRecibo.objects.create(
                recibo=recibo,
                obligacion=obl,
                concepto=obl.concepto,
                periodo=obl.periodo,
                subtotal=obl.saldo_pendiente
            )
            # Liquidar obligación
            obl.estado = EstadoObligacion.PAGADA
            obl.saldo_pendiente = Decimal('0.00')
            obl.save(update_fields=['estado', 'saldo_pendiente', 'updated_at'])

        # Crear registro de Pago
        Pago.objects.create(
            turno=turno,
            recibo=recibo,
            socio=socio,
            monto=monto_total_cobro,
            metodo_pago=metodo_pago,
            referencia_transaccion=referencia_transaccion.strip(),
            fecha_pago=recibo.fecha_emision
        )

        # Actualizar acumuladores del turno
        if metodo_pago == MetodoPago.EFECTIVO:
            turno.total_efectivo_sistema += monto_total_cobro
        else:
            turno.total_digital_sistema += monto_total_cobro
        turno.save(update_fields=['total_efectivo_sistema', 'total_digital_sistema', 'updated_at'])

    # Registrar auditoría completa (P6)
    registrar_auditoria(
        modulo='CAJA',
        accion='COBRO_VENTANILLA',
        resultado="EXITO",
        usuario=usuario_cajero,
        entidad_afectada='Recibo',
        registro_id=str(recibo.id),
        detalle={
            'recibo_id': recibo.id,
            'numero_recibo': recibo.numero_recibo,
            'socio_codigo': socio.codigo,
            'monto_total': str(recibo.monto_total),
            'metodo_pago': recibo.metodo_pago,
            'cantidad_obligaciones': len(obligaciones),
            'obligaciones_ids': [o.id for o in obligaciones]
        },
        ip_origen=ip_origen
    )

    return recibo


def anular_recibo(
    recibo: Recibo,
    usuario_supervisor: Usuario,
    motivo: str,
    ip_origen: Optional[str] = None
) -> Recibo:
    """
    Revierte atómicamente un recibo emitido y restablece las obligaciones al estado PENDIENTE.
    Sección 9.4 de la fuente y Regla R-DOM-17. Prohíbe borrado físico (P5).
    """
    if recibo.estado == EstadoRecibo.ANULADO:
        raise ValidationError("El recibo ya se encuentra anulado.")

    if not motivo or len(motivo.strip()) < 10:
        raise ValidationError("Debe proporcionar una justificación documentada de al menos 10 caracteres.")

    with transaction.atomic():
        # Bloqueo pesimista del recibo
        recibo = Recibo.objects.select_for_update().get(pk=recibo.pk)

        detalles = list(recibo.detalles.select_related('obligacion').all())

        # Revertir cada obligación asociada a PENDIENTE
        for det in detalles:
            obl = Obligacion.objects.select_for_update().get(pk=det.obligacion_id)
            obl.estado = EstadoObligacion.PENDIENTE
            obl.saldo_pendiente = obl.monto
            obl.save(update_fields=['estado', 'saldo_pendiente', 'updated_at'])

        # Si el turno sigue abierto, ajustar acumuladores de caja
        turno = CajaTurno.objects.select_for_update().get(pk=recibo.turno_id)
        if turno.estado == EstadoTurnoCaja.ABIERTA:
            if recibo.metodo_pago == MetodoPago.EFECTIVO:
                turno.total_efectivo_sistema = max(Decimal('0.00'), turno.total_efectivo_sistema - recibo.monto_total)
            else:
                turno.total_digital_sistema = max(Decimal('0.00'), turno.total_digital_sistema - recibo.monto_total)
            turno.save(update_fields=['total_efectivo_sistema', 'total_digital_sistema', 'updated_at'])

        # Actualizar estado de recibo a ANULADO
        recibo.estado = EstadoRecibo.ANULADO
        recibo.fecha_anulacion = timezone.now()
        recibo.usuario_anulacion = usuario_supervisor
        recibo.motivo_anulacion = motivo.strip()
        recibo.save(update_fields=['estado', 'fecha_anulacion', 'usuario_anulacion', 'motivo_anulacion'])

    # Auditoría P6
    registrar_auditoria(
        modulo='CAJA',
        accion='ANULACION_RECIBO',
        resultado="EXITO",
        usuario=usuario_supervisor,
        entidad_afectada='Recibo',
        registro_id=str(recibo.id),
        detalle={
            'estado_anterior': EstadoRecibo.EMITIDO,
            'estado': EstadoRecibo.ANULADO,
            'numero_recibo': recibo.numero_recibo,
            'motivo_anulacion': recibo.motivo_anulacion,
            'obligaciones_revertidas': [d.obligacion_id for d in detalles]
        },
        ip_origen=ip_origen
    )

    return recibo
