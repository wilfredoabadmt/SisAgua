import pytest
from django.urls import reverse
from apps.seguridad.models import Usuario, Rol
from apps.seguridad.services import sugerir_username, generar_clave_temporal
from apps.core.models import BitacoraAuditoria

@pytest.mark.django_db
def test_sugerir_username_y_manejo_de_colisiones():
    """
    Verifica que se sugiera la inicial del nombre y primer apellido,
    limpiando acentos y resolviendo colisiones (US5, FR-009).
    """
    # 1. Caso base con acentos
    sug1 = sugerir_username("Ángel", "Pérez")
    assert sug1 == "aperez"

    # 2. Si ya existe un usuario con ese username
    Usuario.objects.create_user(
        username="aperez",
        password="ClaveTemporal123!",
        nombres="Angel",
        apellido_paterno="Perez",
        ci_numero="1234567"
    )

    sug2 = sugerir_username("Ana", "Perez")
    assert sug2 == "aperez1"

    # 3. Segunda colisión
    Usuario.objects.create_user(
        username="aperez1",
        password="ClaveTemporal123!",
        nombres="Ana",
        apellido_paterno="Perez",
        ci_numero="7654321"
    )
    sug3 = sugerir_username("Antonio", "Perez")
    assert sug3 == "aperez2"


@pytest.mark.django_db
def test_generar_clave_temporal_cumple_entropia():
    """
    Verifica que la clave temporal generada contenga mayúsculas, minúsculas y números (US5).
    """
    clave = generar_clave_temporal(10)
    assert len(clave) == 10
    assert any(c.isupper() for c in clave)
    assert any(c.islower() for c in clave)
    assert any(c.isdigit() for c in clave)


@pytest.mark.django_db
def test_alta_usuario_y_emision_de_ficha(client, usuario_admin, rol_cajero):
    """
    Verifica el flujo de alta de usuario administrativo con forzado de clave inicial (US5).
    """
    client.force_login(usuario_admin)
    url_crear = reverse('seguridad:usuarios_list')

    response = client.post(url_crear, {
        'nombres': 'Beatriz',
        'apellido_paterno': 'Flores',
        'apellido_materno': 'Mamani',
        'ci_numero': '88776655',
        'ci_expedido': 'LP',
        'username': '', # Deberá autogenerar 'bflores'
        'rol': rol_cajero.id,
        'telefono': '70011223',
        'email': 'bflores@comite.bo'
    }, follow=True)

    assert response.status_code == 200
    
    # Comprobar usuario en base de datos
    user_creado = Usuario.objects.get(ci_numero='88776655')
    assert user_creado.username == 'bflores'
    assert user_creado.requiere_cambio_clave is True
    assert user_creado.rol == rol_cajero

    # Comprobar redirección a la ficha de enrolamiento
    assert response.redirect_chain[-1][0] == reverse('seguridad:ficha_enrolamiento')
    assert "Ficha Confidencial de Entrega" in response.content.decode('utf-8')
    assert "bflores" in response.content.decode('utf-8')


@pytest.mark.django_db
def test_usuario_actualiza_su_perfil(client, usuario_cajero):
    """
    Verifica el autoservicio de perfil para modificar teléfono y correo (US6).
    """
    client.force_login(usuario_cajero)
    url_perfil = reverse('seguridad:perfil')

    response = client.post(url_perfil, {
        'telefono': '79988776',
        'email': 'cajero.nuevo@comite.bo'
    }, follow=True)

    assert response.status_code == 200
    usuario_cajero.refresh_from_db()
    assert usuario_cajero.telefono == '79988776'
    assert usuario_cajero.email == 'cajero.nuevo@comite.bo'

    # Auditoría
    assert BitacoraAuditoria.objects.filter(
        modulo='PERFIL',
        accion='MODIFICAR',
        resultado='EXITO',
        usuario=usuario_cajero
    ).exists()

