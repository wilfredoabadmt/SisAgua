from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from .models import Zona, Socio, EstadoSocio
from .forms import ZonaForm, SocioForm
from .services import registrar_socio


# ==============================================================================
# VISTAS DE ZONAS
# ==============================================================================

@requiere_permiso('ZONAS', 'VER')
def zonas_list(request):
    buscar = request.GET.get('buscar', '').strip()
    zonas = Zona.objects.all()
    if buscar:
        zonas = zonas.filter(Q(codigo__icontains=buscar) | Q(nombre__icontains=buscar))
    return render(request, 'socios/zonas_list.html', {'zonas': zonas, 'buscar': buscar})


@requiere_permiso('ZONAS', 'CREAR')
def zona_crear(request):
    if request.method == 'POST':
        form = ZonaForm(request.POST)
        if form.is_valid():
            zona = form.save()
            registrar_auditoria(
                modulo='ZONAS',
                accion='CREAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Zona',
                registro_id=str(zona.id),
                detalle={'codigo': zona.codigo, 'nombre': zona.nombre},
                request=request
            )
            messages.success(request, f"Zona '{zona.nombre}' creada exitosamente.")
            return redirect('socios:zonas_list')
    else:
        form = ZonaForm()
    return render(request, 'socios/zona_form.html', {'form': form, 'titulo': 'Nueva Zona Territorial'})


@requiere_permiso('ZONAS', 'MODIFICAR')
def zona_editar(request, pk):
    zona = get_object_or_404(Zona, pk=pk)
    previos = {'codigo': zona.codigo, 'nombre': zona.nombre, 'activo': zona.activo}
    if request.method == 'POST':
        form = ZonaForm(request.POST, instance=zona)
        if form.is_valid():
            zona = form.save()
            registrar_auditoria(
                modulo='ZONAS',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Zona',
                registro_id=str(zona.id),
                detalle={'previos': previos, 'nuevos': {'codigo': zona.codigo, 'nombre': zona.nombre, 'activo': zona.activo}},
                request=request
            )
            messages.success(request, f"Zona '{zona.nombre}' actualizada exitosamente.")
            return redirect('socios:zonas_list')
    else:
        form = ZonaForm(instance=zona)
    return render(request, 'socios/zona_form.html', {'form': form, 'titulo': f'Editar Zona: {zona.nombre}', 'zona': zona})


@requiere_permiso('ZONAS', 'MODIFICAR')
def zona_desactivar(request, pk):
    zona = get_object_or_404(Zona, pk=pk)
    if request.method == 'POST':
        zona.activo = False
        zona.save(update_fields=['activo', 'updated_at'])
        registrar_auditoria(
            modulo='ZONAS',
            accion='MODIFICAR',
            resultado='EXITO',
            usuario=request.user,
            entidad_afectada='Zona',
            registro_id=str(zona.id),
            detalle={'motivo': 'Desactivación lógica de zona', 'activo': False},
            request=request
        )
        messages.warning(request, f"Zona '{zona.nombre}' desactivada lógicamente (Principio P5).")
    return redirect('socios:zonas_list')


# ==============================================================================
# VISTAS DE SOCIOS
# ==============================================================================

@requiere_permiso('SOCIOS', 'VER')
def socios_list(request):
    buscar = request.GET.get('buscar', '').strip()
    zona_id = request.GET.get('zona', '')
    estado = request.GET.get('estado', '')

    socios = Socio.objects.select_related('zona').all()
    if buscar:
        socios = socios.filter(
            Q(codigo__icontains=buscar) |
            Q(ci__icontains=buscar) |
            Q(nombres__icontains=buscar) |
            Q(apellidos__icontains=buscar)
        )
    if zona_id:
        socios = socios.filter(zona_id=zona_id)
    if estado:
        socios = socios.filter(estado=estado)

    zonas = Zona.objects.filter(activo=True)
    return render(request, 'socios/socios_list.html', {
        'socios': socios,
        'zonas': zonas,
        'buscar': buscar,
        'zona_seleccionada': zona_id,
        'estado_seleccionado': estado,
        'estados': EstadoSocio.choices
    })


@requiere_permiso('SOCIOS', 'CREAR')
def socio_crear(request):
    if request.method == 'POST':
        form = SocioForm(request.POST)
        if form.is_valid():
            try:
                socio = registrar_socio(
                    datos=form.cleaned_data,
                    usuario=request.user,
                    ip_origen=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.success(request, f"Socio {socio.nombre_completo} ({socio.codigo}) registrado con membresía oficial.")
                return redirect('socios:socio_detalle', pk=socio.pk)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = SocioForm()
    return render(request, 'socios/socio_form.html', {'form': form, 'titulo': 'Alta de Nuevo Socio'})


@requiere_permiso('SOCIOS', 'VER')
def socio_detalle(request, pk):
    socio = get_object_or_404(Socio.objects.select_related('zona'), pk=pk)
    # Medidores asignados actualmente (activos) e histórico
    asignaciones_activas = socio.asignaciones_medidor.filter(activo=True).select_related('medidor')
    asignaciones_historicas = socio.asignaciones_medidor.filter(activo=False).select_related('medidor')
    # Obligaciones del socio
    obligaciones = socio.obligaciones.select_related('servicio').order_by('-fecha_emision')
    total_deuda = sum(ob.saldo_pendiente for ob in obligaciones if ob.estado == 'PENDIENTE')

    return render(request, 'socios/socio_detalle.html', {
        'socio': socio,
        'asignaciones_activas': asignaciones_activas,
        'asignaciones_historicas': asignaciones_historicas,
        'obligaciones': obligaciones,
        'total_deuda': total_deuda,
        'estados': EstadoSocio.choices
    })


@requiere_permiso('SOCIOS', 'MODIFICAR')
def socio_editar(request, pk):
    socio = get_object_or_404(Socio, pk=pk)
    previos = {
        'ci': socio.ci_formateado,
        'nombres': socio.nombres,
        'apellidos': socio.apellidos,
        'direccion': socio.direccion,
        'telefono': socio.telefono,
        'estado': socio.estado
    }
    if request.method == 'POST':
        form = SocioForm(request.POST, instance=socio)
        if form.is_valid():
            socio = form.save()
            registrar_auditoria(
                modulo='SOCIOS',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Socio',
                registro_id=str(socio.id),
                detalle={
                    'previos': previos,
                    'nuevos': {
                        'ci': socio.ci_formateado,
                        'nombres': socio.nombres,
                        'apellidos': socio.apellidos,
                        'direccion': socio.direccion,
                        'telefono': socio.telefono,
                        'estado': socio.estado
                    }
                },
                request=request
            )
            messages.success(request, f"Datos de {socio.nombre_completo} actualizados exitosamente.")
            return redirect('socios:socio_detalle', pk=socio.pk)
    else:
        form = SocioForm(instance=socio)
    return render(request, 'socios/socio_form.html', {'form': form, 'titulo': f'Editar Socio: {socio.nombre_completo}', 'socio': socio})


@requiere_permiso('SOCIOS', 'MODIFICAR')
def socio_cambiar_estado(request, pk):
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('nuevo_estado')
        motivo = request.POST.get('motivo', '').strip()
        if nuevo_estado in EstadoSocio.values and nuevo_estado != socio.estado:
            antiguo_estado = socio.estado
            socio.estado = nuevo_estado
            socio.save(update_fields=['estado', 'updated_at'])
            registrar_auditoria(
                modulo='SOCIOS',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Socio',
                registro_id=str(socio.id),
                detalle={'antiguo_estado': antiguo_estado, 'nuevo_estado': nuevo_estado, 'motivo': motivo},
                request=request
            )
            messages.info(request, f"Estado del socio {socio.codigo} actualizado a {socio.get_estado_display()} (R-DOM-05: deudas preservadas).")
    return redirect('socios:socio_detalle', pk=socio.pk)


@requiere_permiso('SOCIOS', 'MODIFICAR')
def socio_habilitar_portal(request, pk):
    """
    Genera credenciales de acceso al portal institucional para el socio.
    Sección 11 y 12.1 de la fuente.
    """
    from .services import habilitar_acceso_portal
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        try:
            user, clave_temp = habilitar_acceso_portal(
                socio_id=socio.pk,
                usuario_operador=request.user,
                ip_origen=obtener_ip_cliente(request)
            )
            messages.success(
                request,
                f"Acceso al portal habilitado para {socio.nombre_completo}. "
                f"Usuario: {user.username} | Contraseña temporal: {clave_temp}"
            )
        except ValidationError as e:
            messages.error(request, str(e.message if hasattr(e, 'message') else e))
    return redirect('socios:socio_detalle', pk=socio.pk)
