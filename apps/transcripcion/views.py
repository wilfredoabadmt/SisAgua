import csv
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from apps.core.decorators import requiere_permiso
from apps.core.services import obtener_ip_cliente
from apps.configuracion.models import Institucion
from apps.socios.models import Socio, Zona
from .models import LoteTranscripcion, EstadoLote, TranscripcionLectura, EstadoTranscripcion
from .forms import (
    LoteTranscripcionForm, TranscripcionLecturaForm,
    ObservarTranscripcionForm, RechazarTranscripcionForm, RegularizarDeudaForm
)
from .services import (
    crear_lote_transcripcion, transcribir_lectura,
    validar_transcripcion, observar_transcripcion,
    rechazar_transcripcion, regularizar_deuda_historica,
    calcular_metricas_lote
)


@requiere_permiso('TRANSCRIPCION', 'VER')
def lotes_list(request):
    """
    Panel principal de lotes documentales y métricas consolidadas de migración.
    Secciones 8.1 y 8.6 de la fuente.
    """
    lotes = LoteTranscripcion.objects.select_related('responsable').all()

    # Añadir métricas en memoria para cada lote
    for l in lotes:
        l.metricas = calcular_metricas_lote(l)

    # Métricas globales consolidadas
    qs_total = TranscripcionLectura.objects.all()
    total_registros = qs_total.count()
    total_validados = qs_total.filter(estado=EstadoTranscripcion.VALIDADO).count()
    total_migrados = qs_total.filter(estado=EstadoTranscripcion.MIGRADO).count()
    total_observados = qs_total.filter(estado=EstadoTranscripcion.OBSERVADO).count()
    total_transcritos = qs_total.filter(estado=EstadoTranscripcion.TRANSCRITO).count()

    avance_global_pct = 0.0
    if total_registros > 0:
        avance_global_pct = round(((total_validados + total_migrados) / total_registros) * 100, 1)

    return render(request, 'transcripcion/lotes_list.html', {
        'lotes': lotes,
        'total_registros': total_registros,
        'total_validados': total_validados,
        'total_migrados': total_migrados,
        'total_observados': total_observados,
        'total_transcritos': total_transcritos,
        'avance_global_pct': avance_global_pct
    })


@requiere_permiso('TRANSCRIPCION', 'CREAR')
def lote_crear(request):
    """Alta de nuevo lote o cuaderno físico de transcripción."""
    if request.method == 'POST':
        form = LoteTranscripcionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            ip = obtener_ip_cliente(request)
            try:
                lote = crear_lote_transcripcion(
                    codigo=cd['codigo'],
                    nombre=cd['nombre'],
                    fuente_documental=cd['fuente_documental'],
                    responsable=request.user,
                    periodo_predeterminado=cd['periodo_predeterminado'],
                    total_estimado=cd['total_estimado'],
                    observaciones=cd['observaciones'],
                    ip_origen=ip
                )
                messages.success(request, f"¡Lote '{lote.codigo}' creado exitosamente! Puede comenzar a transcribir.")
                return redirect('transcripcion:lote_detalle', pk=lote.pk)
            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = LoteTranscripcionForm()

    return render(request, 'transcripcion/lote_form.html', {
        'form': form
    })


@requiere_permiso('TRANSCRIPCION', 'VER')
def lote_detalle(request, pk):
    """
    Detalle del lote, cuadro de avance y tabla de filas digitadas con filtros.
    """
    lote = get_object_or_404(LoteTranscripcion.objects.select_related('responsable'), pk=pk)
    metricas = calcular_metricas_lote(lote)

    estado_filtro = request.GET.get('estado', '').strip()
    buscar = request.GET.get('buscar', '').strip()

    registros = TranscripcionLectura.objects.filter(lote=lote).select_related(
        'socio', 'socio__zona', 'medidor', 'transcrito_por', 'validado_por', 'obligacion_regularizada'
    ).order_by('-id')

    if estado_filtro:
        registros = registros.filter(estado=estado_filtro)
    if buscar:
        registros = registros.filter(
            Q(codigo__icontains=buscar) |
            Q(socio__codigo__icontains=buscar) |
            Q(socio__ci__icontains=buscar) |
            Q(socio__nombres__icontains=buscar) |
            Q(socio__apellidos__icontains=buscar) |
            Q(referencia_foja__icontains=buscar)
        )

    return render(request, 'transcripcion/lote_detalle.html', {
        'lote': lote,
        'metricas': metricas,
        'registros': registros[:100],
        'estado_filtro': estado_filtro,
        'buscar': buscar,
        'estados': EstadoTranscripcion.choices,
        'form_observar': ObservarTranscripcionForm(),
        'form_rechazar': RechazarTranscripcionForm(),
        'form_regularizar': RegularizarDeudaForm()
    })


@requiere_permiso('TRANSCRIPCION', 'CREAR')
def transcripcion_capturar(request, lote_id):
    """
    Formulario de captura de lecturas y deudas históricas fila a fila.
    """
    lote = get_object_or_404(LoteTranscripcion, pk=lote_id)
    if lote.estado == EstadoLote.CERRADO:
        messages.error(request, "El lote seleccionado se encuentra cerrado para nuevas transcripciones.")
        return redirect('transcripcion:lote_detalle', pk=lote.id)

    if request.method == 'POST':
        form = TranscripcionLecturaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            ip = obtener_ip_cliente(request)
            try:
                registro = transcribir_lectura(
                    lote=lote,
                    socio=cd['socio'],
                    medidor=cd['medidor'],
                    periodo=cd['periodo'],
                    lectura_anterior=cd['lectura_anterior'],
                    lectura_actual=cd['lectura_actual'],
                    importe_documentado=cd['importe_documentado'],
                    referencia_foja=cd['referencia_foja'],
                    usuario=request.user,
                    observaciones=cd['observaciones'],
                    ip_origen=ip
                )
                messages.success(request, f"Registro {registro.codigo} guardado exitosamente ({registro.get_estado_display()}).")

                # Si el usuario hace clic en "Guardar y Continuar", se queda en la captura
                if 'guardar_continuar' in request.POST:
                    return redirect('transcripcion:transcripcion_capturar', lote_id=lote.id)
                return redirect('transcripcion:lote_detalle', pk=lote.id)

            except ValidationError as e:
                messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        form = TranscripcionLecturaForm(initial={
            'periodo': lote.periodo_predeterminado
        })

    return render(request, 'transcripcion/captura_form.html', {
        'lote': lote,
        'form': form
    })


@requiere_permiso('TRANSCRIPCION', 'VALIDAR')
def transcripcion_validar_view(request, pk):
    """Aprobación formal de un registro histórico por supervisor."""
    if request.method != 'POST':
        return redirect('transcripcion:lotes_list')

    registro = get_object_or_404(TranscripcionLectura, pk=pk)
    ip = obtener_ip_cliente(request)
    try:
        validar_transcripcion(
            transcripcion=registro,
            supervisor=request.user,
            observaciones="Validación conforme en sistema.",
            ip_origen=ip
        )
        messages.success(request, f"Registro {registro.codigo} validado formalmente.")
    except ValidationError as e:
        messages.error(request, str(e.message if hasattr(e, 'message') else e))

    return redirect('transcripcion:lote_detalle', pk=registro.lote_id)


@requiere_permiso('TRANSCRIPCION', 'VALIDAR')
def transcripcion_observar_view(request, pk):
    """Marcar registro con observaciones justificadas."""
    if request.method != 'POST':
        return redirect('transcripcion:lotes_list')

    registro = get_object_or_404(TranscripcionLectura, pk=pk)
    form = ObservarTranscripcionForm(request.POST)
    if form.is_valid():
        motivo = form.cleaned_data['motivo']
        ip = obtener_ip_cliente(request)
        try:
            observar_transcripcion(registro, request.user, motivo, ip)
            messages.warning(request, f"Registro {registro.codigo} marcado como OBSERVADO.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        for err in form.errors.values():
            messages.error(request, err)

    return redirect('transcripcion:lote_detalle', pk=registro.lote_id)


@requiere_permiso('TRANSCRIPCION', 'VALIDAR')
def transcripcion_rechazar_view(request, pk):
    """Descarte definitivo de registro histórico erróneo o sin respaldo (P5)."""
    if request.method != 'POST':
        return redirect('transcripcion:lotes_list')

    registro = get_object_or_404(TranscripcionLectura, pk=pk)
    form = RechazarTranscripcionForm(request.POST)
    if form.is_valid():
        motivo = form.cleaned_data['motivo']
        ip = obtener_ip_cliente(request)
        try:
            rechazar_transcripcion(registro, request.user, motivo, ip)
            messages.info(request, f"Registro {registro.codigo} RECHAZADO formalmente.")
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        for err in form.errors.values():
            messages.error(request, err)

    return redirect('transcripcion:lote_detalle', pk=registro.lote_id)


@requiere_permiso('TRANSCRIPCION', 'VALIDAR')
def transcripcion_regularizar_view(request, pk):
    """
    Regularización a Obligacion económica exigible en caja con respaldo documentado (R-DOM-19).
    """
    if request.method != 'POST':
        return redirect('transcripcion:lotes_list')

    registro = get_object_or_404(TranscripcionLectura, pk=pk)
    form = RegularizarDeudaForm(request.POST)
    if form.is_valid():
        motivo = form.cleaned_data['motivo_respaldo']
        ip = obtener_ip_cliente(request)
        try:
            obligacion = regularizar_deuda_historica(
                transcripcion=registro,
                usuario_autorizador=request.user,
                motivo_respaldo=motivo,
                ip_origen=ip
            )
            messages.success(
                request,
                f"¡Deuda histórica regularizada exitosamente! Se generó la Obligación #{obligacion.id} por Bs {obligacion.monto} "
                f"para el socio {registro.socio.codigo}, disponible ahora para cobro en caja."
            )
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
    else:
        for err in form.errors.values():
            messages.error(request, err)

    return redirect('transcripcion:lote_detalle', pk=registro.lote_id)


@requiere_permiso('TRANSCRIPCION', 'VER')
def reporte_transcripcion_view(request):
    """
    Reporte imprimible y exportable en CSV de avance de transcripción y deudas regularizadas.
    Sección 8.5 de la fuente funcional.
    """
    lote_id = request.GET.get('lote', '').strip()
    zona_id = request.GET.get('zona', '').strip()
    estado = request.GET.get('estado', '').strip()
    periodo = request.GET.get('periodo', '').strip()
    formato = request.GET.get('format', '').strip().lower()

    registros = TranscripcionLectura.objects.select_related(
        'lote', 'socio', 'socio__zona', 'medidor', 'transcrito_por', 'validado_por', 'obligacion_regularizada'
    ).order_by('-fecha_transcripcion')

    if lote_id:
        registros = registros.filter(lote_id=lote_id)
    if zona_id:
        registros = registros.filter(socio__zona_id=zona_id)
    if estado:
        registros = registros.filter(estado=estado)
    if periodo:
        registros = registros.filter(periodo=periodo)

    # Exportación a formato CSV
    if formato == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="reporte_transcripcion_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Código Transcripción', 'Lote', 'Zona', 'Código Socio', 'CI', 'Nombres y Apellidos',
            'Medidor', 'Periodo', 'Lectura Anterior', 'Lectura Actual', 'Consumo (m3)',
            'Importe Documentado (Bs)', 'Referencia Foja', 'Estado', 'Transcriptor',
            'Fecha Transcripción', 'Validador', 'Fecha Validación', 'Obligación Regularizada ID'
        ])

        for r in registros:
            writer.writerow([
                r.codigo,
                r.lote.codigo,
                r.socio.zona.nombre,
                r.socio.codigo,
                r.socio.ci,
                f"{r.socio.apellidos}, {r.socio.nombres}",
                r.medidor.codigo if r.medidor else 'Sin medidor',
                r.periodo,
                r.lectura_anterior if r.lectura_anterior is not None else '',
                r.lectura_actual if r.lectura_actual is not None else '',
                r.consumo_calculado if r.consumo_calculado is not None else '',
                r.importe_documentado if r.importe_documentado is not None else '',
                r.referencia_foja,
                r.get_estado_display(),
                r.transcrito_por.username,
                r.fecha_transcripcion.strftime('%d/%m/%Y %H:%M'),
                r.validado_por.username if r.validado_por else '',
                r.fecha_validacion.strftime('%d/%m/%Y %H:%M') if r.fecha_validacion else '',
                r.obligacion_regularizada_id or ''
            ])
        return response

    institucion = Institucion.get_solo()
    lotes = LoteTranscripcion.objects.all()
    zonas = Zona.objects.filter(activo=True)

    return render(request, 'transcripcion/reporte_transcripcion.html', {
        'institucion': institucion,
        'registros': registros[:200],
        'lotes': lotes,
        'zonas': zonas,
        'lote_seleccionado': lote_id,
        'zona_seleccionada': zona_id,
        'estado_seleccionado': estado,
        'periodo_seleccionado': periodo,
        'estados': EstadoTranscripcion.choices
    })

