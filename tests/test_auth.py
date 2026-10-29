import pytest
from django.urls import reverse
from django.utils import timezone
from apps.seguridad.models import Usuario, Rol

@pytest.fixture
def usuario_con_clave_temporal(db):
    """Crea un usuario que requiere cambio obligatorio de clave."""
    return Usuario.objects.create_user(
        username="mlopez",
        password="TemporalPassword123!",
        nombres="Maria",
        apellido_paterno="Lopez",
        ci_numero="4567890",
        requiere_cambio_clave=True
    )


@pytest.mark.django_db
def test_login_exitoso_redirige_a_cambio_clave_si_es_temporal(client, usuario_con_clave_temporal):
    """
    Escenario 1: Al ingresar con clave temporal, el sistema debe autenticar y redirigir
    forzosamente a la pantalla de cambio de contraseña (US1).
    """
    url_login = reverse('seguridad:login')
    response = client.post(url_login, {
        'username': 'mlopez',
        'password': 'TemporalPassword123!'
    }, follow=True)

    assert response.status_code == 200
    # Comprobar que fue redirigido a cambiar-contrasena
    assert response.redirect_chain[-1][0] == reverse('seguridad:cambiar_contrasena')


@pytest.mark.django_db
def test_middleware_bloquea_otras_rutas_si_requiere_cambio_clave(client, usuario_con_clave_temporal):
    """
    Escenario 2: El middleware ForzarCambioClaveMiddleware intercepta cualquier intento
    de navegar a otra ruta protegida y redirige a cambiar clave (US1, FR-003).
    """
    client.force_login(usuario_con_clave_temporal)
    
    # Intentar acceder al dashboard
    response = client.get(reverse('seguridad:dashboard'), follow=True)
    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse('seguridad:cambiar_contrasena')


@pytest.mark.django_db
def test_rechazo_de_contrasena_igual_al_ci_o_debil(client, usuario_con_clave_temporal):
    """
    Escenario 3: La nueva contraseña no puede coincidir con el carnet de identidad
    ni tener menos de 8 caracteres (Principio P7, FR-003).
    """
    client.force_login(usuario_con_clave_temporal)
    url_cambio = reverse('seguridad:cambiar_contrasena')

    # Intento 1: Menos de 8 caracteres
    res1 = client.post(url_cambio, {
        'password_nuevo': 'Ab1!',
        'password_confirmar': 'Ab1!'
    })
    assert res1.status_code == 200
    assert usuario_con_clave_temporal.check_password('TemporalPassword123!') is True

    # Intento 2: Igual al carnet de identidad
    res2 = client.post(url_cambio, {
        'password_nuevo': '4567890',
        'password_confirmar': '4567890'
    })
    assert res2.status_code == 200
    assert usuario_con_clave_temporal.check_password('TemporalPassword123!') is True


@pytest.mark.django_db
def test_cambio_exitoso_de_clave_desactiva_bandera_forzada(client, usuario_con_clave_temporal):
    """
    Escenario 4: Con una clave válida, se actualiza el hash Argon2id y se desactiva
    la bandera requiere_cambio_clave, permitiendo navegar libremente.
    """
    client.force_login(usuario_con_clave_temporal)
    url_cambio = reverse('seguridad:cambiar_contrasena')

    response = client.post(url_cambio, {
        'password_nuevo': 'NuevaClaveSegura2026!',
        'password_confirmar': 'NuevaClaveSegura2026!'
    }, follow=True)

    assert response.status_code == 200
    usuario_con_clave_temporal.refresh_from_db()
    assert usuario_con_clave_temporal.requiere_cambio_clave is False
    assert usuario_con_clave_temporal.check_password('NuevaClaveSegura2026!') is True

    # Ahora sí debe poder acceder al dashboard sin redirección forzada
    res_dash = client.get(reverse('seguridad:dashboard'))
    assert res_dash.status_code == 200


@pytest.mark.django_db
def test_bloqueo_por_fuerza_bruta_tras_cinco_intentos(client, usuario_con_clave_temporal):
    """
    Escenario 5: Al quinto intento fallido consecutivo, la cuenta se bloquea por 15 minutos (FR-004).
    """
    url_login = reverse('seguridad:login')

    for i in range(5):
        client.post(url_login, {
            'username': 'mlopez',
            'password': 'ClaveErroneaIncorrecta'
        })

    usuario_con_clave_temporal.refresh_from_db()
    assert usuario_con_clave_temporal.intentos_fallidos == 5
    assert usuario_con_clave_temporal.bloqueado_hasta is not None
    assert usuario_con_clave_temporal.esta_bloqueado() is True

    # Intento 6 con clave correcta debe ser rechazado por estar bloqueada
    response = client.post(url_login, {
        'username': 'mlopez',
        'password': 'TemporalPassword123!'
    })
    assert response.status_code == 200
    assert '_auth_user_id' not in client.session

