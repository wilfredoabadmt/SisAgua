"""
Servicios de dominio para el módulo de seguridad, gestión de usuarios y credenciales.
"""
import secrets
import string
import unicodedata
from .models import Usuario

def limpiar_texto(texto: str) -> str:
    """Elimina tildes, diacríticos y caracteres especiales."""
    if not texto:
        return ""
    texto_norm = unicodedata.normalize('NFKD', texto)
    return "".join(c for c in texto_norm if not unicodedata.combining(c)).strip()


def sugerir_username(nombres: str, apellido_paterno: str) -> str:
    """
    Genera un nombre de usuario normalizado basado en la inicial del nombre
    y el primer apellido (ej. Maria Lopez -> mlopez).
    Resuelve colisiones de forma determinística agregando un sufijo incremental (mlopez1, mlopez2).
    """
    nom = limpiar_texto(nombres)
    ape = limpiar_texto(apellido_paterno)
    
    if not nom or not ape:
        return "usuario"

    base = f"{nom[0]}{ape}".lower()
    # Eliminar espacios internos si existieran
    base = "".join(c for c in base if c.isalnum())
    
    if not base:
        base = "usuario"

    # Verificar existencia en base de datos
    candidato = base
    contador = 1
    
    while Usuario.objects.filter(username__iexact=candidato).exists():
        candidato = f"{base}{contador}"
        contador += 1

    return candidato


def generar_clave_temporal(longitud: int = 10) -> str:
    """
    Genera una contraseña temporal aleatoria de alta entropía (P7, FR-003).
    Garantiza al menos una letra mayúscula, una minúscula y un dígito.
    """
    caracteres = string.ascii_letters + string.digits + "@#$*&"
    while True:
        clave = "".join(secrets.choice(caracteres) for _ in range(longitud))
        if (any(c.islower() for c in clave) and 
            any(c.isupper() for c in clave) and 
            any(c.isdigit() for c in clave)):
            return clave

