"""
Vistas del núcleo de SisAgua y consulta de auditoría.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import BitacoraAuditoria
from .decorators import requiere_permiso

@login_required
@requiere_permiso(modulo='institucion', accion='ver')
def auditoria_list_view(request):
    """Consulta paginada e inalterable de la bitácora de auditoría."""
    queryset = BitacoraAuditoria.objects.all().select_related('usuario')

    # Filtros
    modulo = request.GET.get('modulo')
    if modulo:
        queryset = queryset.filter(modulo__iexact=modulo)
        
    accion = request.GET.get('accion')
    if accion:
        queryset = queryset.filter(accion__iexact=accion)

    resultado = request.GET.get('resultado')
    if resultado:
        queryset = queryset.filter(resultado__iexact=resultado)

    fecha_desde = request.GET.get('fecha_desde')
    if fecha_desde:
        queryset = queryset.filter(fecha_hora_utc__date__gte=fecha_desde)

    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_hasta:
        queryset = queryset.filter(fecha_hora_utc__date__lte=fecha_hasta)

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/auditoria_list.html', {
        'page_obj': page_obj,
        'filtros': request.GET,
    })

