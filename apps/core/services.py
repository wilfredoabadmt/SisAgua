"""
Servicios transversales de auditoría y seguridad para SisAgua.
Garantiza el Principio P6 (Auditoría Verificable) y P7 (Cero Secretos en Auditoría).
"""
import copy
from typing import Optional, Dict, Any
from django.http import HttpRequest
from .models import BitacoraAuditoria

CAMPOS_SENSIBLES = {
    'password', 'password_hash', 'password_actual', 'password_nuevo', 
    'password_confirmar', 'token', 'secret', 'jwt', 'authorization', 
    'csrfmiddlewaretoken', 'clave_temporal_generada'
}

def sanitizar_detalle(detalle: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Elimina recursivamente cualquier contraseña, secreto o token antes de persistir
    en la bitácora de auditoría.
    """
    if not isinstance(detalle, dict):
        return {}
    
    limpio = copy.deepcopy(detalle)
    
    def limpiar_diccionario(d):
        if not isinstance(d, dict):
            return
        for k in list(d.keys()):
            if any(sensible in k.lower() for sensible in CAMPOS_SENSIBLES):
                d[k] = "[REDACTADO_POR_SEGURIDAD]"
            elif isinstance(d[k], dict):
                limpiar_diccionario(d[k])
            elif isinstance(d[k], list):
                for item in d[k]:
                    if isinstance(item, dict):
                        limpiar_diccionario(item)

    limpiar_diccionario(limpio)
    return limpio


def obtener_ip_cliente(request: Optional[HttpRequest]) -> Optional[str]:
    """Extrae la dirección IP real del cliente considerando proxies."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_auditoria(
    modulo: str,
    accion: str,
    resultado: str = "EXITO",
    usuario=None,
    entidad_afectada: str = "",
    registro_id: str = "",
    detalle: Optional[Dict[str, Any]] = None,
    ip_origen: Optional[str] = None,
    request: Optional[HttpRequest] = None,
) -> BitacoraAuditoria:
    """
    Punto de entrada oficial para registrar cualquier evento en la bitácora.
    """
    if request:
        if not usuario and hasattr(request, 'user') and request.user.is_authenticated:
            usuario = request.user
        if not ip_origen:
            ip_origen = obtener_ip_cliente(request)

    detalle_limpio = sanitizar_detalle(detalle)

    return BitacoraAuditoria.objects.create(
        usuario=usuario if (usuario and getattr(usuario, 'is_authenticated', False)) else None,
        ip_origen=ip_origen,
        modulo=modulo.upper(),
        accion=accion.upper(),
        resultado=resultado.upper(),
        entidad_afectada=entidad_afectada,
        registro_id=str(registro_id),
        detalle_json=detalle_limpio,
    )

