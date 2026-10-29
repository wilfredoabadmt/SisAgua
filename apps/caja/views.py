from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.decorators import requiere_permiso
from apps.core.services import obtener_ip_cliente
from apps.configuracion.models import Institucion
from apps.socios.models import Socio
from apps.medidores.models import AsignacionMedidor
from apps.servicios.models import Obligacion, EstadoObligacion
from .models import CajaTurno, EstadoTurnoCaja, Recibo, EstadoRecibo, MetodoPago, Pago
from .forms import AperturaTurnoForm, CierreTurnoForm, CobroVentanillaForm, AnularReciboForm
from .services import (
    iniciar_turno_caja, cerrar_turno_caja,
    procesar_cobro, anular_recibo
)


@requiere_permiso('CAJA', 'VER')
def cobros_ventanilla(request):
    """
    Ventanilla principal de cobro.
    Permite buscar socios, inspeccionar deudas y seleccionar obligaciones para liquidar.
    Sección 9.1 y 9.2 de la fuente.
    """
    turno_activo = CajaTurno.objects.filter(
        cajero=request.user,
        estado=EstadoTurnoCaja.ABIERTA
    ).first()

    q = request.GET.get('q', '').strip()
    socio_id = request.GET.get('socio_id', '').strip()

    socio_seleccionado = None
    obligaciones_pendientes = []
    medidores_asociados = []
    recibos_recientes = []
    total_deuda = Decimal('0.00')
    socios_encontrados = []

    if socio_id:
        socio_seleccionado = Socio.objects.filter(pk=socio_id, activo=True).select_related('zona').first()
    elif q:
        # Búsqueda multidimensional: código, CI, nombres, apellidos, medidor
        socios_qs = Socio.objects.filter(activo=True).select_related('zona').filter(
            Q(codigo__icontains=q) |
            Q(ci__icontains=q) |
            Q(nombres__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(asignaciones_medidor__medidor__codigo__icontains=q)
        ).distinct()

        if socios_qs.count() == 1:
            socio_seleccionado = socios_qs.first()
        else:
            socios_encontrados = list(socios_qs[:15])

    if socio_seleccionado:
        hoy = timezone.now().date()
        obligaciones_pendientes = Obligacion.objects.filter(
            socio=socio_seleccionado,
            estado=EstadoObligacion.PENDIENTE
        ).select_related('servicio').order_by('fecha_vencimiento', 'id')

        # Clasificar vencidas
        for o in obligaciones_pendientes:
            o.esta_vencida = o.fecha_vencimiento < hoy

        total_deuda = sum(o.saldo_pendiente for o in obligaciones_pendientes)

        medidores_asociados = AsignacionMedidor.objects.filter(
            socio=socio_seleccionado,
            activo=True
        ).select_related('medidor')

        recibos_recientes = Recibo.objects.filter(
            socio=socio_seleccionado
        ).order_by('-fecha_emision')[:5]

    form_cobro = CobroVentanillaForm(initial={'socio_id': socio_seleccionado.id if socio_seleccionado else ''})

    return render(request, 'caja/cobros.html', {
        'turno_activo': turno_activo,
        'q': q,
        'socio': socio_seleccionado,
        'socios_encontrados': socios_encontrados,
        'obligaciones': obligaciones_pendientes,
        'medidores': medidores_asociados,
        'recibos_recientes': recibos_recientes,
        'total_deuda': total_deuda,
        'form_cobro': form_cobro,
        'metodos_pago': MetodoPago.choices
    })


@requiere_permiso('CAJA', 'CREAR')
def procesar_cobro_view(request):
    """
    Procesamiento transaccional de cobro en ventanilla.
    R-DOM-15 (No pagos parciales), R-DOM-16 (Cobro atómico), R-DOM-17 (Recibo oficial).
    """
    if request.method != 'POST':
        return redirect('caja:cobros')

    turno_activo = CajaTurno.objects.filter(
        cajero=request.user,
        estado=EstadoTurnoCaja.ABIERTA
    ).first()

    if not turno_activo:
        messages.error(request, "Debe abrir un turno de caja antes de realizar cobros.")
        return redirect('caja:turno_apertura')

    socio_id = request.POST.get('socio_id')
    metodo_pago = request.POST.get('metodo_pago', MetodoPago.EFECTIVO)
    referencia = request.POST.get('referencia_transaccion', '').strip()
    obligaciones_ids_raw = request.POST.getlist('obligaciones_ids')

    if not socio_id or not obligaciones_ids_raw:
        messages.error(request, "Debe seleccionar al menos una obligación para procesar el cobro.")
        return redirect(f"/caja/cobros/?socio_id={socio_id}" if socio_id else 'caja:cobros')

    try:
        socio = get_object_or_404(Socio, pk=socio_id)
        obligaciones_ids = [int(oid) for oid in obligaciones_ids_raw]
        ip = obtener_ip_cliente(request)

        recibo = procesar_cobro(
            turno=turno_activo,
            socio=socio,
            obligaciones_ids=obligaciones_ids,
            metodo_pago=metodo_pago,
            referencia_transaccion=referencia,
            cajero=request.user,
            ip_origen=ip
        )

        messages.success(request, f"¡Cobro exitoso! Se ha emitido el Recibo Oficial {recibo.numero_recibo} por Bs {recibo.monto_total}.")
        return redirect('caja:recibo_detalle', pk=recibo.pk)

    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, 'message') else e))
        return redirect(f"/caja/cobros/?socio_id={socio_id}")
    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado al procesar el cobro: {str(e)}")
        return redirect(f"/caja/cobros/?socio_id={socio_id}")


@requiere_permiso('CAJA', 'VER')
def recibo_detalle(request, pk):
    """
    Vista y comprobante oficial de cobranza con código QR apto para impresión.
    Sección 9.4 y Regla R-DOM-17.
    """
    recibo = get_object_or_404(
        Recibo.objects.select_related('socio', 'socio__zona', 'cajero', 'turno', 'usuario_anulacion').prefetch_related('detalles__obligacion'),
        pk=pk
    )
    institucion = Institucion.get_solo()
    anular_form = AnularReciboForm()

    return render(request, 'caja/recibo_detalle.html', {
        'recibo': recibo,
        'institucion': institucion,
        'anular_form': anular_form
    })


@requiere_permiso('CAJA', 'ANULAR')
def recibo_anular_view(request, pk):
    """
    Anulación formal de recibo por supervisor con justificación documentada (R-DOM-17, P5).
    """
    if request.method != 'POST':
        return redirect('caja:recibo_detalle', pk=pk)

    recibo = get_object_or_404(Recibo, pk=pk)
    form = AnularReciboForm(request.POST)

    if form.is_valid():
        motivo = form.cleaned_data['motivo']
        ip = obtener_ip_cliente(request)
        try:
            anular_recibo(
                recibo=recibo,
                usuario_supervisor=request.user,
                motivo=motivo,
                ip_origen=ip
            )
            messages.success(request, f"El Recibo {recibo.numero_recibo} fue ANULADO formalmente y las obligaciones se restauraron a estado PENDIENTE.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
        except Exception as e:
            messages.error(request, f"Error al anular el recibo: {str(e)}")
    else:
        for error in form.errors.values():
            messages.error(request, error)

    return redirect('caja:recibo_detalle', pk=pk)


@requiere_permiso('CAJA', 'VER')
def recibos_list(request):
    """
    Listado histórico de recibos emitidos y anulados.
    """
    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()

    recibos = Recibo.objects.select_related('socio', 'cajero').order_by('-fecha_emision')

    if buscar:
        recibos = recibos.filter(
            Q(numero_recibo__icontains=buscar) |
            Q(socio__codigo__icontains=buscar) |
            Q(socio__ci__icontains=buscar) |
            Q(socio__nombres__icontains=buscar) |
            Q(socio__apellidos__icontains=buscar)
        )
    if estado:
        recibos = recibos.filter(estado=estado)
    if fecha_desde:
        recibos = recibos.filter(fecha_emision__date__gte=fecha_desde)
    if fecha_hasta:
        recibos = recibos.filter(fecha_emision__date__lte=fecha_hasta)

    return render(request, 'caja/recibos_list.html', {
        'recibos': recibos[:100],
        'buscar': buscar,
        'estado_seleccionado': estado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estados': EstadoRecibo.choices
    })


@requiere_permiso('CAJA', 'CREAR')
def turno_apertura(request):
    """
    Apertura de turno de caja con fondo inicial.
    """
    turno_existente = CajaTurno.objects.filter(
        cajero=request.user,
        estado=EstadoTurnoCaja.ABIERTA
    ).first()

    if turno_existente:
        messages.info(request, f"Ya tienes un turno de caja abierto iniciado el {turno_existente.fecha_apertura.strftime('%d/%m/%Y %H:%M')}.")
        return redirect('caja:cobros')

    if request.method == 'POST':
        form = AperturaTurnoForm(request.POST)
        if form.is_valid():
            monto_apertura = form.cleaned_data['monto_apertura']
            ip = obtener_ip_cliente(request)
            try:
                turno = iniciar_turno_caja(
                    usuario=request.user,
                    monto_apertura=monto_apertura,
                    ip_origen=ip
                )
                messages.success(request, f"¡Turno de caja #{turno.id} abierto exitosamente con fondo de Bs {monto_apertura}!")
                return redirect('caja:cobros')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = AperturaTurnoForm(initial={'monto_apertura': Decimal('0.00')})

    return render(request, 'caja/turno_apertura.html', {
        'form': form
    })


@requiere_permiso('CAJA', 'CERRAR')
def turno_cierre(request):
    """
    Arqueo y cierre de sesión de caja activa.
    Sección 9.5 de la fuente.
    """
    turno = CajaTurno.objects.filter(
        cajero=request.user,
        estado=EstadoTurnoCaja.ABIERTA
    ).first()

    if not turno:
        messages.warning(request, "No cuentas con un turno de caja abierto actualmente.")
        return redirect('caja:turnos_list')

    # Calcular totales actuales en tiempo real para mostrar en el formulario
    pagos_turno = Pago.objects.filter(turno=turno, recibo__estado=EstadoRecibo.EMITIDO)
    total_efectivo = sum((p.monto for p in pagos_turno if p.metodo_pago == MetodoPago.EFECTIVO), Decimal('0.00'))
    total_digital = sum((p.monto for p in pagos_turno if p.metodo_pago != MetodoPago.EFECTIVO), Decimal('0.00'))
    efectivo_esperado = turno.monto_apertura + total_efectivo

    if request.method == 'POST':
        form = CierreTurnoForm(request.POST)
        if form.is_valid():
            monto_declarado = form.cleaned_data['monto_declarado_efectivo']
            observaciones = form.cleaned_data['observaciones_cierre']
            ip = obtener_ip_cliente(request)
            try:
                cerrar_turno_caja(
                    turno=turno,
                    monto_declarado_efectivo=monto_declarado,
                    observaciones=observaciones,
                    cerrado_por=request.user,
                    ip_origen=ip
                )
                messages.success(request, f"¡Turno #{turno.id} cerrado exitosamente! Arqueo completado.")
                return redirect('caja:turnos_list')
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = CierreTurnoForm(initial={'monto_declarado_efectivo': efectivo_esperado})

    return render(request, 'caja/turno_cierre.html', {
        'turno': turno,
        'total_efectivo': total_efectivo,
        'total_digital': total_digital,
        'efectivo_esperado': efectivo_esperado,
        'form': form
    })


@requiere_permiso('CAJA', 'VER')
def turnos_list(request):
    """
    Historial de turnos de caja para supervisión y auditoría.
    """
    turnos = CajaTurno.objects.select_related('cajero', 'cerrado_por').order_by('-fecha_apertura')[:50]
    return render(request, 'caja/turnos_list.html', {
        'turnos': turnos
    })
