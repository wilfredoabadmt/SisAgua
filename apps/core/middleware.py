"""
Middleware de seguridad y control de sesión para SisAgua.
Garantiza el forzado de cambio de clave temporal en el primer acceso (FR-003).
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

RUTAS_EXENTAS = [
    '/perfil/cambiar-contrasena/',
    '/logout/',
    '/static/',
    '/media/',
]

class ForzarCambioClaveMiddleware:
    """
    Si el usuario tiene activa la bandera 'requiere_cambio_clave', bloquea cualquier
    navegación o acción en el sistema y redirige forzosamente a la pantalla de cambio
    de contraseña hasta que establezca una clave privada y segura.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Comprobar si el usuario requiere cambio forzado de credencial
            if getattr(request.user, 'requiere_cambio_clave', False):
                path = request.path_info
                
                # Permitir rutas exentas necesarias para cambiar la clave o cerrar sesión
                es_exenta = any(path.startswith(ruta) for ruta in RUTAS_EXENTAS)
                
                if not es_exenta:
                    messages.warning(
                        request,
                        "Por motivos de seguridad, debe cambiar su contraseña temporal antes de continuar utilizando el sistema."
                    )
                    return redirect('seguridad:cambiar_contrasena')

        return self.get_response(request)

