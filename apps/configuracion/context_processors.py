"""
Procesadores de contexto globales para SisAgua.
Inyecta datos institucionales y menús dinámicos filtrados por permisos.
"""
from django.core.cache import cache
from .models import Institucion, Menu

def datos_institucion(request):
    """
    Inyecta la configuración institucional en todas las plantillas.
    """
    try:
        institucion = Institucion.get_solo()
    except Exception:
        institucion = None
        
    return {
        'institucion': institucion,
    }


def menu_navegacion(request):
    """
    Construye el árbol de menús dinámico para el usuario autenticado.
    Filtra los menús superiores y submenús según los permisos del rol del usuario.
    """
    if not request.user.is_authenticated:
        return {'menu_navegacion': []}

    user = request.user
    
    # Si es superusuario, tiene acceso a todos los menús activos
    if user.is_superuser:
        permisos_set = None
    else:
        rol = getattr(user, 'rol', None)
        if not rol or not rol.activo:
            return {'menu_navegacion': []}
        # Crear conjunto de permisos: {"MODULO:ACCION"}
        permisos_set = {
            f"{p.modulo.upper()}:{p.accion.upper()}" 
            for p in rol.permisos.all()
        }

    # Obtener menús de primer nivel activos
    menus_raiz = Menu.objects.filter(padre__isnull=True, activo=True).prefetch_related('submenus').order_by('orden')
    
    menu_filtrado = []
    for m in menus_raiz:
        # Verificar permiso del menú raíz si lo tuviera
        if m.permiso_requerido and permisos_set is not None:
            perm_key = f"{m.permiso_requerido.modulo.upper()}:{m.permiso_requerido.accion.upper()}"
            if perm_key not in permisos_set:
                continue

        # Filtrar submenús
        submenus_validos = []
        for sub in m.submenus.filter(activo=True).order_by('orden'):
            if sub.permiso_requerido and permisos_set is not None:
                sub_key = f"{sub.permiso_requerido.modulo.upper()}:{sub.permiso_requerido.accion.upper()}"
                if sub_key not in permisos_set:
                    continue
            submenus_validos.append(sub)

        # Si el menú raíz no tiene ruta y no le quedó ningún submenú visible, no mostrarlo
        if not m.ruta and not submenus_validos:
            continue

        menu_filtrado.append({
            'menu': m,
            'submenus': submenus_validos
        })

    return {
        'menu_navegacion': menu_filtrado
    }

