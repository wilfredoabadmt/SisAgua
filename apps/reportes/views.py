import csv
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from apps.configuracion.models import Institucion
from apps.socios.models import Socio, Zona
from apps.seguridad.models import Usuario
from apps.caja.models import MetodoPago
from .services import (
    obtener_reporte_deudores,
    obtener_reporte_recaudacion,
    obtener_reporte_consumo,
    obtener_reporte_zonas,
    obtener_reporte_membresias,
    obtener_estado_cuenta_socio
)


def _verificar_permiso_exportar(user, request, reporte_nombre: str):
    if user.is_superuser:
        return True
    rol = getattr(user, 'rol', None)
    tiene = False
    if rol and rol.activo:
        tiene = rol.permisos.filter(modulo__iexact='REPORTES', accion__iexact='EXPORTAR').exists()
    if not tiene:
        registrar_auditoria(
            modulo='REPORTES',
            accion='ACCESS_DENIED',
            resultado='FALLO',
            usuario=user,
            request=request,
            detalle={'permiso_requerido': 'REPORTES:EXPORTAR', 'reporte': reporte_nombre, 'ruta': request.path}
        )
        raise PermissionDenied("No tiene autorización para exportar reportes analíticos a CSV.")

    registrar_auditoria(
        modulo='REPORTES',
        accion='EXPORTAR',
        resultado='EXITO',
        usuario=user,
        request=request,
        detalle={'reporte': reporte_nombre, 'formato': 'CSV'}
    )
    return True


@requiere_permiso('REPORTES', 'VER')
def dashboard(request):
    """
    Panel ejecutivo central con métricas resumen del sistema.
    """
    institucion = Institucion.get_solo()
    deudores = obtener_reporte_deudores()
    recaudacion = obtener_reporte_recaudacion()
    zonas = obtener_reporte_zonas()

    return render(request, 'reportes/dashboard.html', {
        'institucion': institucion,
        'deudores': deudores,
        'recaudacion': recaudacion,
        'zonas': zonas,
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_deudores(request):
    """
    Reporte consolidado de deudores y cartera en mora.
    Sección 10.1 de la fuente funcional.
    """
    zona_id = request.GET.get('zona')
    antiguedad = request.GET.get('antiguedad')
    solo_vencidas = request.GET.get('solo_vencidas') in ['1', 'true', 'True']
    formato = request.GET.get('format')

    zona_val = int(zona_id) if zona_id and zona_id.isdigit() else None
    antiguedad_val = int(antiguedad) if antiguedad and antiguedad.isdigit() else None

    datos = obtener_reporte_deudores(
        zona_id=zona_val,
        antiguedad_minima=antiguedad_val,
        solo_vencidas=solo_vencidas
    )

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, 'Deudores')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_deudores_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Código', 'CI', 'Socio', 'Zona', 'Medidores', 'Deuda Agua (Bs)', 'Deuda Membresía (Bs)', 'Otros (Bs)', 'Total Pendiente (Bs)', 'Mora Vencida (Bs)', 'Meses Mora', 'Periodos'])
        for d in datos['deudores']:
            writer.writerow([
                d['socio'].codigo,
                d['socio'].ci,
                f"{d['socio'].nombres} {d['socio'].apellidos}",
                d['zona'].nombre if d['zona'] else 'Sin Zona',
                d['cantidad_medidores'],
                f"{d['deuda_agua']:.2f}",
                f"{d['deuda_membresia']:.2f}",
                f"{d['deuda_otros']:.2f}",
                f"{d['total_pendiente']:.2f}",
                f"{d['importe_vencido']:.2f}",
                d['antiguedad_meses'],
                d['periodos_str']
            ])
        return response

    zonas = Zona.objects.filter(activo=True).order_by('nombre')
    return render(request, 'reportes/deudores.html', {
        'institucion': Institucion.get_solo(),
        'datos': datos,
        'zonas': zonas,
        'zona_seleccionada': zona_val,
        'antiguedad_seleccionada': antiguedad_val,
        'solo_vencidas': solo_vencidas
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_recaudacion(request):
    """
    Conciliación de recaudación por medio de pago y discriminación de anulados.
    Sección 10.5 de la fuente funcional.
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    cajero_id = request.GET.get('cajero')
    metodo = request.GET.get('metodo')
    formato = request.GET.get('format')

    cajero_val = int(cajero_id) if cajero_id and cajero_id.isdigit() else None

    datos = obtener_reporte_recaudacion(
        fecha_desde=fecha_desde or None,
        fecha_hasta=fecha_hasta or None,
        cajero_id=cajero_val,
        metodo_pago=metodo or None
    )

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, 'Recaudacion')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_recaudacion_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nro Recibo', 'Fecha Emisión', 'Socio', 'Cajero', 'Método Pago', 'Monto Total (Bs)', 'Estado'])
        for r in datos['recibos']:
            writer.writerow([
                r.numero_recibo,
                r.fecha_emision.strftime('%Y-%m-%d %H:%M'),
                f"{r.socio.nombres} {r.socio.apellidos}",
                r.cajero.get_full_name() or r.cajero.username,
                r.get_metodo_pago_display(),
                f"{r.monto_total:.2f}",
                r.get_estado_display()
            ])
        return response

    cajeros = Usuario.objects.filter(activo=True).order_by('apellido_paterno', 'nombres')
    metodos = MetodoPago.choices

    return render(request, 'reportes/recaudacion.html', {
        'institucion': Institucion.get_solo(),
        'datos': datos,
        'cajeros': cajeros,
        'metodos': metodos,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cajero_seleccionado': cajero_val,
        'metodo_seleccionado': metodo
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_consumo(request):
    """
    Reporte de consumo volumétrico y anomalías.
    Sección 10.4 de la fuente funcional.
    """
    periodo = request.GET.get('periodo')
    zona_id = request.GET.get('zona')
    formato = request.GET.get('format')

    zona_val = int(zona_id) if zona_id and zona_id.isdigit() else None
    datos = obtener_reporte_consumo(periodo=periodo or None, zona_id=zona_val)

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, 'Consumo')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_consumo_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Periodo', 'Medidor', 'Socio', 'Zona', 'Lectura Anterior', 'Lectura Actual', 'Consumo (m³)', 'Estado'])
        for l in datos['lecturas']:
            writer.writerow([
                l.periodo,
                l.medidor.codigo,
                f"{l.socio.nombres} {l.socio.apellidos}",
                l.socio.zona.nombre if l.socio.zona else '',
                f"{l.lectura_anterior:.2f}",
                f"{l.lectura_actual:.2f}",
                f"{l.consumo_m3:.2f}",
                l.get_estado_display()
            ])
        return response

    zonas = Zona.objects.filter(activo=True).order_by('nombre')
    return render(request, 'reportes/consumo.html', {
        'institucion': Institucion.get_solo(),
        'datos': datos,
        'zonas': zonas,
        'periodo_seleccionado': datos['periodo'],
        'zona_seleccionada': zona_val
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_zonas(request):
    """
    Reporte de balance territorial por zona.
    Sección 10.2 de la fuente funcional.
    """
    periodo = request.GET.get('periodo')
    formato = request.GET.get('format')

    zonas_resumen = obtener_reporte_zonas(periodo=periodo or None)

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, 'Zonas')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_zonas_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Código', 'Zona', 'Total Socios', 'Activos', 'Inactivos', 'Medidores', 'Facturado (Bs)', 'Recaudado (Bs)', 'Mora (Bs)', 'Eficacia (%)'])
        for z in zonas_resumen:
            writer.writerow([
                z['zona'].codigo,
                z['zona'].nombre,
                z['total_socios'],
                z['socios_activos'],
                z['socios_inactivos'],
                z['total_medidores'],
                f"{z['total_facturado']:.2f}",
                f"{z['total_recaudado']:.2f}",
                f"{z['total_mora']:.2f}",
                f"{z['eficacia_pct']:.1f}%"
            ])
        return response

    return render(request, 'reportes/zonas.html', {
        'institucion': Institucion.get_solo(),
        'zonas_resumen': zonas_resumen,
        'periodo_seleccionado': periodo or ''
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_membresias(request):
    """
    Reporte de cuotas de incorporación/afiliación única de socios.
    Sección 10.6 de la fuente funcional.
    """
    zona_id = request.GET.get('zona')
    estado = request.GET.get('estado')
    formato = request.GET.get('format')

    zona_val = int(zona_id) if zona_id and zona_id.isdigit() else None
    datos = obtener_reporte_membresias(zona_id=zona_val, estado_filtro=estado or None)

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, 'Membresias')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_membresias_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Código Socio', 'Socio', 'Zona', 'Fecha Emisión', 'Monto (Bs)', 'Saldo Pendiente (Bs)', 'Estado'])
        for m in datos['membresias']:
            writer.writerow([
                m.socio.codigo,
                f"{m.socio.nombres} {m.socio.apellidos}",
                m.socio.zona.nombre if m.socio.zona else '',
                m.fecha_emision.strftime('%Y-%m-%d'),
                f"{m.monto:.2f}",
                f"{m.saldo_pendiente:.2f}",
                m.get_estado_display()
            ])
        return response

    zonas = Zona.objects.filter(activo=True).order_by('nombre')
    return render(request, 'reportes/membresias.html', {
        'institucion': Institucion.get_solo(),
        'datos': datos,
        'zonas': zonas,
        'zona_seleccionada': zona_val,
        'estado_seleccionado': estado or ''
    })


@requiere_permiso('REPORTES', 'VER')
def reporte_socio_estado_cuenta(request, socio_id: int):
    """
    Estado de cuenta individual 360° del socio.
    Sección 10.3 de la fuente funcional.
    """
    formato = request.GET.get('format')
    datos = obtener_estado_cuenta_socio(socio_id=socio_id)

    if formato == 'csv':
        _verificar_permiso_exportar(request.user, request, f'EstadoCuenta_SOC_{socio_id}')
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="estado_cuenta_socio_{socio_id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['--- ESTADO DE CUENTA SOCIO ---'])
        writer.writerow(['Socio:', f"{datos['socio'].nombres} {datos['socio'].apellidos}", 'Código:', datos['socio'].codigo, 'CI:', datos['socio'].ci])
        writer.writerow(['Total Facturado (Bs):', f"{datos['total_facturado']:.2f}", 'Total Pagado (Bs):', f"{datos['total_pagado']:.2f}", 'Saldo Deudor (Bs):', f"{datos['total_pendiente']:.2f}"])
        writer.writerow([])
        writer.writerow(['--- OBLIGACIONES ---'])
        writer.writerow(['Periodo', 'Servicio', 'Vencimiento', 'Monto (Bs)', 'Saldo (Bs)', 'Estado'])
        for o in datos['obligaciones']:
            writer.writerow([o.periodo, o.servicio.nombre, o.fecha_vencimiento.strftime('%Y-%m-%d'), f"{o.monto:.2f}", f"{o.saldo_pendiente:.2f}", o.get_estado_display()])
        return response

    return render(request, 'reportes/socio_estado_cuenta.html', {
        'institucion': Institucion.get_solo(),
        'datos': datos
    })
