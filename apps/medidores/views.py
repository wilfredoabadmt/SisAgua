from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from .models import Medidor, AsignacionMedidor, EstadoMedidor
from .forms import MedidorForm, AsignarMedidorForm, RetirarMedidorForm
from .services import generar_codigo_medidor, asignar_medidor, desasignar_medidor


@requiere_permiso('MEDIDORES', 'VER')
def medidores_list(request):
    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '')

    medidores = Medidor.objects.all()
    if buscar:
        medidores = medidores.filter(
            Q(codigo__icontains=buscar) |
            Q(numero_serie__icontains=buscar) |
            Q(marca__icontains=buscar)
        )
    if estado:
        medidores = medidores.filter(estado=estado)

    return render(request, 'medidores/medidores_list.html', {
        'medidores': medidores,
        'buscar': buscar,
        'estado_seleccionado': estado,
        'estados': EstadoMedidor.choices
    })


@requiere_permiso('MEDIDORES', 'CREAR')
def medidor_crear(request):
    if request.method == 'POST':
        form = MedidorForm(request.POST)
        if form.is_valid():
            medidor = form.save(commit=False)
            if not medidor.codigo:
                medidor.codigo = generar_codigo_medidor()
            medidor.save()
            registrar_auditoria(
                modulo='MEDIDORES',
                accion='CREAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Medidor',
                registro_id=str(medidor.id),
                detalle={
                    'codigo': medidor.codigo,
                    'numero_serie': medidor.numero_serie,
                    'lectura_inicial': str(medidor.lectura_inicial)
                },
                request=request
            )
            messages.success(request, f"Medidor '{medidor.codigo}' (Serie: {medidor.numero_serie}) registrado.")
            return redirect('medidores:medidores_list')
    else:
        form = MedidorForm()
    return render(request, 'medidores/medidor_form.html', {'form': form, 'titulo': 'Alta de Medidor en Inventario'})


@requiere_permiso('MEDIDORES', 'MODIFICAR')
def medidor_editar(request, pk):
    medidor = get_object_or_404(Medidor, pk=pk)
    previos = {
        'codigo': medidor.codigo,
        'numero_serie': medidor.numero_serie,
        'estado': medidor.estado
    }
    if request.method == 'POST':
        form = MedidorForm(request.POST, instance=medidor)
        if form.is_valid():
            medidor = form.save()
            registrar_auditoria(
                modulo='MEDIDORES',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Medidor',
                registro_id=str(medidor.id),
                detalle={'previos': previos, 'nuevos': {'codigo': medidor.codigo, 'numero_serie': medidor.numero_serie, 'estado': medidor.estado}},
                request=request
            )
            messages.success(request, f"Medidor '{medidor.codigo}' actualizado exitosamente.")
            return redirect('medidores:medidores_list')
    else:
        form = MedidorForm(instance=medidor)
    return render(request, 'medidores/medidor_form.html', {'form': form, 'titulo': f'Editar Medidor: {medidor.codigo}', 'medidor': medidor})


@requiere_permiso('MEDIDORES', 'MODIFICAR')
def medidor_asignar(request, pk):
    medidor = get_object_or_404(Medidor, pk=pk)
    if request.method == 'POST':
        form = AsignarMedidorForm(request.POST)
        if form.is_valid():
            try:
                asignacion = asignar_medidor(
                    medidor=medidor,
                    socio=form.cleaned_data['socio'],
                    lectura_instalacion=form.cleaned_data['lectura_instalacion'],
                    fecha_asignacion=form.cleaned_data['fecha_asignacion'],
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.success(
                    request,
                    f"Medidor {medidor.codigo} asignado exitosamente al socio {asignacion.socio.nombre_completo} (R-DOM-03)."
                )
                return redirect('socios:socio_detalle', pk=asignacion.socio.pk)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = AsignarMedidorForm(initial={
            'lectura_instalacion': medidor.lectura_inicial
        })
    return render(request, 'medidores/asignar_form.html', {'form': form, 'medidor': medidor})


@requiere_permiso('MEDIDORES', 'MODIFICAR')
def asignacion_retirar(request, pk):
    asignacion = get_object_or_404(AsignacionMedidor.objects.select_related('medidor', 'socio'), pk=pk)
    if request.method == 'POST':
        form = RetirarMedidorForm(request.POST)
        if form.is_valid():
            try:
                desasignar_medidor(
                    asignacion=asignacion,
                    lectura_retiro=form.cleaned_data['lectura_retiro'],
                    fecha_retiro=form.cleaned_data['fecha_retiro'],
                    motivo_retiro=form.cleaned_data['motivo_retiro'],
                    nuevo_estado=form.cleaned_data['nuevo_estado_medidor'],
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.warning(
                    request,
                    f"Medidor {asignacion.medidor.codigo} retirado con lectura final de {form.cleaned_data['lectura_retiro']} m³ (R-DOM-04)."
                )
                return redirect('socios:socio_detalle', pk=asignacion.socio.pk)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = RetirarMedidorForm(initial={
            'lectura_retiro': asignacion.lectura_instalacion
        })
    return render(request, 'medidores/retirar_form.html', {'form': form, 'asignacion': asignacion})

