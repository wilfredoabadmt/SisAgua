from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.decorators import requiere_permiso
from apps.core.services import registrar_auditoria
from .models import Institucion, Menu
from .forms import InstitucionForm

@login_required
@requiere_permiso(modulo='institucion', accion='modificar')
def institucion_config_view(request):
    """
    Vista de parametrización institucional (US2).
    """
    institucion = Institucion.get_solo()

    if request.method == 'POST':
        form = InstitucionForm(request.POST, request.FILES, instance=institucion)
        if form.is_valid():
            inst_guardada = form.save()
            registrar_auditoria(
                modulo='INSTITUCION',
                accion='MODIFICAR',
                resultado='EXITO',
                usuario=request.user,
                entidad_afectada='Institucion',
                registro_id=inst_guardada.id,
                detalle={'nombre': inst_guardada.nombre, 'telefono': inst_guardada.telefono},
                request=request
            )
            messages.success(request, "Datos de la institución actualizados correctamente.")
            return redirect('configuracion:institucion_config')
    else:
        form = InstitucionForm(instance=institucion)

    return render(request, 'configuracion/institucion.html', {
        'form': form,
        'institucion': institucion,
    })


@login_required
@requiere_permiso(modulo='menus', accion='ver')
def menus_list_view(request):
    """
    Listado y administración de opciones de menú (US4).
    """
    menus_raiz = Menu.objects.filter(padre__isnull=True).prefetch_related('submenus').order_by('orden')
    return render(request, 'configuracion/menus_list.html', {
        'menus': menus_raiz,
    })

