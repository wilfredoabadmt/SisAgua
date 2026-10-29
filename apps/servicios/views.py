from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from .models import Servicio, Tarifario, TramoTarifario
from .forms import ServicioForm, TarifarioForm, TramoTarifarioForm


# ==============================================================================
# VISTAS DE SERVICIOS
# ==============================================================================

@requiere_permiso('SERVICIOS', 'VER')
def servicios_list(request):
    servicios = Servicio.objects.all()
    return render(request, 'servicios/servicios_list.html', {'servicios': servicios})


@requiere_permiso('SERVICIOS', 'CREAR')
def servicio_crear(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save()
            registrar_auditoria(
                modulo='SERVICIOS',
                accion='CREAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Servicio',
                registro_id=str(servicio.id),
                detalle={
                    'codigo': servicio.codigo,
                    'nombre': servicio.nombre,
                    'modalidad_cobro': servicio.modalidad_cobro
                },
                request=request
            )
            messages.success(request, f"Servicio '{servicio.nombre}' registrado exitosamente.")
            return redirect('servicios:servicios_list')
    else:
        form = ServicioForm()
    return render(request, 'servicios/servicio_form.html', {'form': form, 'titulo': 'Nuevo Servicio Comunitario'})


@requiere_permiso('SERVICIOS', 'MODIFICAR')
def servicio_editar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    previos = {'codigo': servicio.codigo, 'nombre': servicio.nombre, 'activo': servicio.activo}
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            servicio = form.save()
            registrar_auditoria(
                modulo='SERVICIOS',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Servicio',
                registro_id=str(servicio.id),
                detalle={'previos': previos, 'nuevos': {'codigo': servicio.codigo, 'nombre': servicio.nombre, 'activo': servicio.activo}},
                request=request
            )
            messages.success(request, f"Servicio '{servicio.nombre}' actualizado exitosamente.")
            return redirect('servicios:servicios_list')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'servicios/servicio_form.html', {'form': form, 'titulo': f'Editar Servicio: {servicio.nombre}', 'servicio': servicio})


# ==============================================================================
# VISTAS DE TARIFARIOS
# ==============================================================================

@requiere_permiso('TARIFARIO', 'VER')
def tarifarios_list(request):
    tarifarios = Tarifario.objects.select_related('servicio').all()
    return render(request, 'servicios/tarifarios_list.html', {'tarifarios': tarifarios})


@requiere_permiso('TARIFARIO', 'CREAR')
def tarifario_crear(request):
    if request.method == 'POST':
        form = TarifarioForm(request.POST)
        if form.is_valid():
            tarifario = form.save()
            registrar_auditoria(
                modulo='TARIFARIO',
                accion='CREAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Tarifario',
                registro_id=str(tarifario.id),
                detalle={
                    'nombre': tarifario.nombre,
                    'tarifa_basica': str(tarifario.tarifa_basica),
                    'consumo_minimo_m3': str(tarifario.consumo_minimo_m3),
                    'precio_adicional_m3': str(tarifario.precio_adicional_m3),
                    'vigencia_desde': str(tarifario.fecha_vigencia_desde)
                },
                request=request
            )
            messages.success(request, f"Tarifario '{tarifario.nombre}' creado exitosamente (R-DOM-10: No Retroactividad).")
            return redirect('servicios:tarifario_detalle', pk=tarifario.pk)
    else:
        form = TarifarioForm()
    return render(request, 'servicios/tarifario_form.html', {'form': form, 'titulo': 'Nuevo Esquema Tarifario'})


@requiere_permiso('TARIFARIO', 'VER')
def tarifario_detalle(request, pk):
    tarifario = get_object_or_404(Tarifario.objects.select_related('servicio'), pk=pk)
    tramos = tarifario.tramos.all()
    tramo_form = TramoTarifarioForm(initial={'orden': tramos.count() + 1})
    return render(request, 'servicios/tarifario_detalle.html', {
        'tarifario': tarifario,
        'tramos': tramos,
        'tramo_form': tramo_form
    })


@requiere_permiso('TARIFARIO', 'MODIFICAR')
def tramo_crear(request, pk):
    tarifario = get_object_or_404(Tarifario, pk=pk)
    if request.method == 'POST':
        form = TramoTarifarioForm(request.POST)
        if form.is_valid():
            tramo = form.save(commit=False)
            tramo.tarifario = tarifario
            tramo.save()
            registrar_auditoria(
                modulo='TARIFARIO',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='TramoTarifario',
                registro_id=str(tramo.id),
                detalle={'tarifario': tarifario.nombre, 'orden': tramo.orden, 'precio': str(tramo.precio_unitario)},
                request=request
            )
            messages.success(request, f"Tramo {tramo.orden} añadido al tarifario.")
    return redirect('servicios:tarifario_detalle', pk=pk)

