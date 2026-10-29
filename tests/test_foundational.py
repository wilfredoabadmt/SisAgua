import pytest
from apps.core.models import BitacoraAuditoria
from apps.core.services import sanitizar_detalle, registrar_auditoria
from apps.configuracion.models import Institucion
from apps.seguridad.models import Rol, Permiso, Usuario

@pytest.mark.django_db
def test_argon2_hasher_default():
    """
    Verifica que las contraseñas se almacenen utilizando Argon2id como hasher primario (P7, T008).
    """
    user = Usuario.objects.create_user(
        username="test_argon",
        password="ClaveSecretaRobusta2026!",
        nombres="Test",
        apellido_paterno="Argon",
        ci_numero="99887766"
    )
    assert user.password.startswith("argon2"), f"La contraseña no usa Argon2: {user.password[:15]}"
    assert user.check_password("ClaveSecretaRobusta2026!") is True
    assert user.check_password("ClaveErronea") is False


@pytest.mark.django_db
def test_sanitizar_auditoria_elimina_secretos():
    """
    Verifica que ninguna contraseña, token o secreto se persista en la bitácora de auditoría (P6, P7, T007).
    """
    detalle_sucio = {
        "usuario": "mlopez",
        "password": "PasswordEnTextoClaro123!",
        "password_nuevo": "NuevaClave456!",
        "token": "secret_jwt_token_xyz",
        "nested": {
            "clave_temporal_generada": "Temp987!",
            "accion_valida": "CAMBIO_ESTADO"
        }
    }
    limpio = sanitizar_detalle(detalle_sucio)
    
    assert limpio["password"] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio["password_nuevo"] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio["token"] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio["nested"]["clave_temporal_generada"] == "[REDACTADO_POR_SEGURIDAD]"
    assert limpio["nested"]["accion_valida"] == "CAMBIO_ESTADO"


@pytest.mark.django_db
def test_registrar_auditoria_servicio():
    """
    Verifica el funcionamiento del servicio unificado registrar_auditoria() (T007).
    """
    reg = registrar_auditoria(
        modulo="CONFIGURACION",
        accion="UPDATE",
        resultado="EXITO",
        entidad_afectada="Institucion",
        registro_id="1",
        detalle={"nombre": "Comité Central", "password": "DebeSerOcultado"}
    )
    
    assert reg.id is not None
    assert reg.modulo == "CONFIGURACION"
    assert reg.accion == "UPDATE"
    assert reg.resultado == "EXITO"
    assert reg.detalle_json["nombre"] == "Comité Central"
    assert reg.detalle_json["password"] == "[REDACTADO_POR_SEGURIDAD]"


@pytest.mark.django_db
def test_institucion_singleton_get_solo():
    """
    Verifica el patrón Singleton para la configuración institucional (P9, T017).
    """
    inst1 = Institucion.get_solo()
    assert inst1.id == 1
    assert inst1.moneda == "Bs"

    inst1.nombre = "Cooperativa El Porvenir"
    inst1.save()

    inst2 = Institucion.get_solo()
    assert inst2.id == 1
    assert inst2.nombre == "Cooperativa El Porvenir"
    assert Institucion.objects.count() == 1

