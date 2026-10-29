"""
Decoradores y Mixins de autorización granular basados en roles (RBAC).
Garantiza el Principio P7 (Verificación forzosa en Servidor).
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from .services import registrar_auditoria

def requiere_permiso(modulo: str, accion: str):
    """
    Decorador para vistas basadas en funciones.
    Verifica que el usuario autenticado tenga el permiso específico (modulo, accion).
    Si se deniega el acceso, registra un evento 'ACCESS_DENIED' en auditoría y lanza PermissionDenied (403).
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())

            # Si es superusuario del sistema, acceso total garantizado
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Verificar a través del rol del usuario
            rol = getattr(request.user, 'rol', None)
            tiene_permiso = False
            
            if rol and rol.activo:
                tiene_permiso = rol.permisos.filter(
                    modulo__iexact=modulo,
                    accion__iexact=accion
                ).exists()

            if not tiene_permiso:
                registrar_auditoria(
                    modulo=modulo,
                    accion="ACCESS_DENIED",
                    resultado="FALLO",
                    usuario=request.user,
                    request=request,
                    detalle={
                        "modulo_solicitado": modulo,
                        "accion_solicitada": accion,
                        "ruta": request.path,
                        "rol_usuario": rol.codigo if rol else "SIN_ROL"
                    }
                )
                raise PermissionDenied(f"Acceso denegado: Se requiere permiso de {accion} en {modulo}.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

