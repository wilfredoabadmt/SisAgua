from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from apps.socios.models import Zona
from apps.medidores.models import Medidor
from apps.servicios.models import Obligacion
from .models import Lectura, EstadoLectura
from .forms import CapturaLecturaForm, CorregirLecturaForm, FacturacionForm
from .services import (
    resolver_lectura_anterior, registrar_lectura,
    corregir_lectura, obtener_historial_proforma,
    facturar_periodo_agua
)


@requiere_permiso('LECTURAS', 'VER')
def lecturas_list(request):
    periodo = request.GET.get('periodo', timezone.now().strftime('%Y-%m')).strip()
    zona_id = request.GET.get('zona', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    lecturas = Lectura.objects.select_related('medidor', 'socio', 'socio__zona', 'lector').filter(periodo=periodo)

    if zona_id:
        lecturas = lecturas.filter(socio__zona_id=zona_id)
    if buscar:
        lecturas = lecturas.filter(
            Q(medidor__codigo__icontains=buscar) |
            Q(socio__codigo__icontains=buscar) |
            Q(socio__nombres__icontains=buscar) |
            Q(socio__apellidos__icontains=buscar)
        )

    zonas = Zona.objects.filter(activo=True)
    return render(request, 'consumo/lecturas_list.html', {
        'lecturas': lecturas,
        'periodo': periodo,
        'zonas': zonas,
        'zona_seleccionada': zona_id,
        'buscar': buscar
    })


@requiere_permiso('LECTURAS', 'CREAR')
def lectura_capturar(request):
    medidor_id = request.GET.get('medidor_id')
    initial = {}
    if medidor_id:
        initial['medidor'] = medidor_id

    if request.method == 'POST':
        form = CapturaLecturaForm(request.POST)
        if form.is_valid():
            try:
                lectura = registrar_lectura(
                    medidor=form.cleaned_data['medidor'],
                    periodo=form.cleaned_data['periodo'],
                    lectura_actual=form.cleaned_data['lectura_actual'],
                    fecha_lectura=form.cleaned_data['fecha_lectura'],
                    observaciones=form.cleaned_data['observaciones'],
                    es_reinicio_contador=form.cleaned_data['es_reinicio_contador'],
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                if lectura.estado == EstadoLectura.OBSERVADA:
                    messages.warning(
                        request,
                        f"Lectura registrada con OBSERVACIÓN para el medidor {lectura.medidor.codigo}. "
                        "No podrá facturarse hasta ser revisada y validada (Regla R-DOM-07 / Principio P10)."
                    )
                    return redirect('consumo:observadas_list')
                else:
                    messages.success(
                        request,
                        f"Lectura registrada con éxito: {lectura.medidor.codigo} | Consumo: {lectura.consumo_m3} m³."
                    )
                    return redirect('consumo:proforma_detalle', pk=lectura.pk)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = CapturaLecturaForm(initial=initial)

    return render(request, 'consumo/captura_form.html', {'form': form, 'titulo': 'Captura Mensual de Lectura'})


@requiere_permiso('LECTURAS', 'VER')
def observadas_list(request):
    periodo = request.GET.get('periodo', timezone.now().strftime('%Y-%m')).strip()
    observadas = Lectura.objects.select_related('medidor', 'socio', 'socio__zona').filter(
        periodo=periodo,
        estado=EstadoLectura.OBSERVADA
    )
    return render(request, 'consumo/observadas_list.html', {
        'observadas': observadas,
        'periodo': periodo
    })


@requiere_permiso('LECTURAS', 'MODIFICAR')
def lectura_corregir(request, pk):
    lectura = get_object_or_404(Lectura.objects.select_related('medidor', 'socio'), pk=pk)
    if request.method == 'POST':
        form = CorregirLecturaForm(request.POST)
        if form.is_valid():
            try:
                corregida = corregir_lectura(
                    lectura=lectura,
                    nueva_lectura=form.cleaned_data['nueva_lectura'],
                    motivo=form.cleaned_data['motivo_correccion'],
                    es_reinicio_contador=form.cleaned_data['es_reinicio_contador'],
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                if corregida.estado == EstadoLectura.CORREGIDA:
                    messages.success(request, f"Lectura de {corregida.medidor.codigo} corregida exitosamente (Nuevo consumo: {corregida.consumo_m3} m³).")
                    return redirect('consumo:lecturas_list')
                else:
                    messages.warning(request, f"La lectura sigue siendo observada: {corregida.motivo_observacion}")
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = CorregirLecturaForm(initial={
            'nueva_lectura': lectura.lectura_actual,
            'motivo_correccion': lectura.motivo_observacion,
            'es_reinicio_contador': lectura.es_reinicio_contador
        })

    return render(request, 'consumo/corregir_form.html', {
        'form': form,
        'lectura': lectura,
        'titulo': f'Corregir Lectura: {lectura.medidor.codigo} ({lectura.periodo})'
    })


@requiere_permiso('LECTURAS', 'VER')
def proforma_detalle(request, pk):
    lectura = get_object_or_404(Lectura.objects.select_related('medidor', 'socio', 'socio__zona'), pk=pk)
    historial_previo = obtener_historial_proforma(lectura.medidor, periodo_actual=lectura.periodo, limite=3)
    return render(request, 'consumo/proforma_detalle.html', {
        'lectura': lectura,
        'historial_previo': historial_previo
    })


@requiere_permiso('CONSUMO', 'GENERAR')
def facturacion_panel(request):
    periodo = request.GET.get('periodo', timezone.now().strftime('%Y-%m')).strip()
    
    total_medidores_instalados = Medidor.objects.filter(estado='INSTALADO', activo=True).count()
    lecturas_periodo = Lectura.objects.filter(periodo=periodo, activo=True)
    leidos_count = lecturas_periodo.count()
    validadas_count = lecturas_periodo.filter(estado__in=[EstadoLectura.VALIDADA, EstadoLectura.CORREGIDA]).count()
    observadas_count = lecturas_periodo.filter(estado=EstadoLectura.OBSERVADA).count()
    pendientes_lectura = max(0, total_medidores_instalados - leidos_count)

    # Obligaciones generadas para este periodo
    obligaciones_periodo = Obligacion.objects.filter(periodo=periodo, servicio__modalidad_cobro='LECTURA_VOLUMETRICA')
    facturados_count = obligaciones_periodo.count()
    monto_total_facturado = obligaciones_periodo.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')

    form = FacturacionForm(initial={'periodo': periodo})

    return render(request, 'consumo/facturacion_panel.html', {
        'periodo': periodo,
        'form': form,
        'total_instalados': total_medidores_instalados,
        'leidos_count': leidos_count,
        'validadas_count': validadas_count,
        'observadas_count': observadas_count,
        'pendientes_lectura': pendientes_lectura,
        'facturados_count': facturados_count,
        'monto_total_facturado': monto_total_facturado,
        'porcentaje_avance': int((leidos_count / total_medidores_instalados * 100)) if total_medidores_instalados > 0 else 0
    })


@requiere_permiso('CONSUMO', 'GENERAR')
def facturacion_ejecutar(request):
    if request.method == 'POST':
        form = FacturacionForm(request.POST)
        if form.is_valid():
            periodo = form.cleaned_data['periodo']
            try:
                resumen = facturar_periodo_agua(
                    periodo=periodo,
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.success(
                    request,
                    f"Facturación del periodo {periodo} completada: "
                    f"{resumen['obligaciones_generadas']} obligaciones emitidas "
                    f"(Total: Bs {resumen['monto_total_bs']}). "
                    f"Omitidas por idempotencia: {resumen['omitidos_idempotencia']}. "
                    f"Observadas pendientes: {resumen['lecturas_observadas_omitidas']}."
                )
                return redirect(f"/consumo/facturacion/?periodo={periodo}")
            except Exception as e:
                messages.error(request, f"Error en facturación: {str(e)}")
                return redirect(f"/consumo/facturacion/?periodo={periodo}")

    return redirect('consumo:facturacion_panel')

