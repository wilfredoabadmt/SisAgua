from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria, obtener_ip_cliente
from apps.configuracion.models import Institucion
from apps.socios.models import Socio, EstadoSocio
from apps.medidores.models import AsignacionMedidor
from apps.consumo.models import Lectura, EstadoLectura
from apps.consumo.services import obtener_historial_proforma
from apps.servicios.models import Obligacion, EstadoObligacion
from apps.caja.models import Recibo, EstadoRecibo
from .forms import ActualizarContactoForm


def _obtener_socio_autenticado(request) -> Socio:
    """
    Obtiene la ficha de socio unívocamente vinculada al usuario autenticado.
    Garantiza el Principio P7 (Aislamiento de Identidad Multitenant a nivel fila).
    """
    socio = getattr(request.user, 'perfil_socio', None)
    if not socio:
        registrar_auditoria(
            modulo='PORTAL',
            accion='ACCESS_DENIED',
            resultado='FALLO',
            usuario=request.user,
            request=request,
            detalle={'motivo': 'Usuario autenticado sin ficha de socio vinculada'}
        )
        raise PermissionDenied("Su cuenta de usuario no está asociada a ningún socio comunitario registrado.")
    return socio


@requiere_permiso('PORTAL', 'VER')
def portal_dashboard(request):
    """
    Panel de bienvenida y resumen integral 360° del socio.
    Sección 11 de la fuente funcional.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    # Medidores activos
    asignaciones_activas = AsignacionMedidor.objects.filter(
        socio=socio, activo=True
    ).select_related('medidor')

    # Última lectura
    ultima_lectura = Lectura.objects.filter(
        socio=socio, activo=True
    ).order_by('-periodo').first()

    # Cuentas por cobrar
    obligaciones_pendientes = Obligacion.objects.filter(
        socio=socio, estado=EstadoObligacion.PENDIENTE
    ).select_related('servicio').order_by('fecha_vencimiento')

    hoy = timezone.now().date()
    total_pendiente = Decimal('0.00')
    total_vencido = Decimal('0.00')
    for o in obligaciones_pendientes:
        total_pendiente += o.saldo_pendiente
        if o.fecha_vencimiento < hoy:
            total_vencido += o.saldo_pendiente

    # Recibos emitidos recientes
    recibos_recientes = Recibo.objects.filter(
        socio=socio, estado=EstadoRecibo.EMITIDO
    ).order_by('-fecha_emision')[:5]

    return render(request, 'portal/dashboard.html', {
        'institucion': institucion,
        'socio': socio,
        'asignaciones_activas': asignaciones_activas,
        'ultima_lectura': ultima_lectura,
        'obligaciones_pendientes': obligaciones_pendientes,
        'total_pendiente': total_pendiente,
        'total_vencido': total_vencido,
        'recibos_recientes': recibos_recientes
    })


@requiere_permiso('PORTAL', 'VER')
def portal_medidores(request):
    """
    Consulta de medidores asignados y lecturas mensuales registradas.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    asignaciones = AsignacionMedidor.objects.filter(
        socio=socio
    ).select_related('medidor').order_by('-activo', '-fecha_asignacion')

    lecturas = Lectura.objects.filter(
        socio=socio, activo=True
    ).select_related('medidor').order_by('-periodo')[:24]

    return render(request, 'portal/medidores.html', {
        'institucion': institucion,
        'socio': socio,
        'asignaciones': asignaciones,
        'lecturas': lecturas
    })


@requiere_permiso('PORTAL', 'VER')
def portal_deudas(request):
    """
    Detalle de obligaciones y mora adeudada.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()
    hoy = timezone.now().date()

    obligaciones = Obligacion.objects.filter(
        socio=socio
    ).select_related('servicio').order_by('-fecha_emision')

    total_pendiente = sum((o.saldo_pendiente for o in obligaciones if o.estado == EstadoObligacion.PENDIENTE), Decimal('0.00'))
    total_vencido = sum((o.saldo_pendiente for o in obligaciones if o.estado == EstadoObligacion.PENDIENTE and o.fecha_vencimiento < hoy), Decimal('0.00'))

    return render(request, 'portal/deudas.html', {
        'institucion': institucion,
        'socio': socio,
        'obligaciones': obligaciones,
        'total_pendiente': total_pendiente,
        'total_vencido': total_vencido,
        'hoy': hoy
    })


@requiere_permiso('PORTAL', 'VER')
def portal_recibos(request):
    """
    Historial de recibos oficiales emitidos a favor del socio.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    recibos = Recibo.objects.filter(
        socio=socio, estado=EstadoRecibo.EMITIDO
    ).order_by('-fecha_emision')

    return render(request, 'portal/recibos.html', {
        'institucion': institucion,
        'socio': socio,
        'recibos': recibos
    })


@requiere_permiso('PORTAL', 'VER')
def portal_recibo_detalle(request, recibo_id: int):
    """
    Visualización e impresión de recibo oficial propio.
    Blindado contra ataques IDOR: sólo accede al recibo si pertenece a su ficha de socio.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    recibo = get_object_or_404(
        Recibo.objects.select_related('cajero', 'turno'),
        pk=recibo_id,
        socio=socio,
        estado=EstadoRecibo.EMITIDO
    )

    detalles = recibo.detalles.all()

    return render(request, 'portal/recibo_detalle.html', {
        'institucion': institucion,
        'socio': socio,
        'recibo': recibo,
        'detalles': detalles
    })


@requiere_permiso('PORTAL', 'VER')
def portal_proforma(request, periodo: str):
    """
    Proforma informativa de medición del periodo (Regla R-DOM-09).
    Comprobante informativo con historial sin validez de recibo oficial.
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    lecturas_periodo = Lectura.objects.filter(
        socio=socio,
        periodo=periodo,
        activo=True
    ).select_related('medidor')

    if not lecturas_periodo.exists():
        messages.warning(request, f"No existe lectura registrada para el periodo {periodo}.")
        return redirect('portal:medidores')

    # Para cada medidor, obtener historial de hasta 3 lecturas anteriores reales
    items_proforma = []
    for l in lecturas_periodo:
        historial = obtener_historial_proforma(l.medidor, periodo, limite=3)
        items_proforma.append({
            'lectura': l,
            'historial': historial
        })

    return render(request, 'portal/proforma.html', {
        'institucion': institucion,
        'socio': socio,
        'periodo': periodo,
        'items_proforma': items_proforma
    })


@requiere_permiso('PORTAL', 'VER')
def portal_perfil(request):
    """
    Consulta de datos personales y actualización de contacto (teléfono y correo).
    """
    socio = _obtener_socio_autenticado(request)
    institucion = Institucion.get_solo()

    if request.method == 'POST':
        form = ActualizarContactoForm(request.POST, instance=socio)
        if form.is_valid():
            socio = form.save()
            # Sincronizar en la cuenta de usuario
            user = request.user
            user.telefono = socio.telefono
            user.email = socio.email
            user.save(update_fields=['telefono', 'email', 'updated_at'])

            registrar_auditoria(
                modulo='PORTAL',
                accion='MODIFICAR_PERFIL',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Socio',
                registro_id=str(socio.id),
                detalle={
                    'telefono': socio.telefono,
                    'email': socio.email,
                    'motivo': 'Actualización autónoma de datos de contacto por el socio'
                },
                request=request
            )
            messages.success(request, "Sus datos de contacto fueron actualizados exitosamente.")
            return redirect('portal:perfil')
    else:
        form = ActualizarContactoForm(instance=socio)

    return render(request, 'portal/perfil.html', {
        'institucion': institucion,
        'socio': socio,
        'form': form
    })

