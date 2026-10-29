import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.configuracion.models import Institucion
from apps.core.models import BitacoraAuditoria

@pytest.mark.django_db
def test_admin_puede_acceder_a_configuracion_institucional(client, usuario_admin, institucion):
    """
    Verifica que un usuario con permiso de 'modificar' en 'institucion' puede acceder (US2).
    """
    client.force_login(usuario_admin)
    url = reverse('configuracion:institucion_config')
    response = client.get(url)
    assert response.status_code == 200
    assert "Parametrización Institucional" in response.content.decode('utf-8')


@pytest.mark.django_db
def test_usuario_sin_permiso_recibe_403_prohibido(client, usuario_cajero, institucion):
    """
    Verifica que un usuario sin permiso en servidor es bloqueado con HTTP 403 (Principio P7, US2).
    """
    client.force_login(usuario_cajero)
    url = reverse('configuracion:institucion_config')
    response = client.get(url)
    assert response.status_code == 403

    # Comprobar que el intento de acceso no autorizado fue auditado
    assert BitacoraAuditoria.objects.filter(
        accion='ACCESS_DENIED',
        modulo='INSTITUCION',
        resultado='FALLO'
    ).exists()


@pytest.mark.django_db
def test_actualizacion_exitosa_de_datos_institucionales_y_auditoria(client, usuario_admin, institucion):
    """
    Verifica que al guardar datos institucionales se actualicen en base de datos
    y se registre el evento en la bitácora de auditoría (US2, Principio P6, P9).
    """
    client.force_login(usuario_admin)
    url = reverse('configuracion:institucion_config')

    response = client.post(url, {
        'nombre': 'Comité de Agua Potable y Alcantarillado Villa Copacabana',
        'direccion': 'Plaza 16 de Julio #45',
        'telefono': '71554433',
        'correo': 'contacto@villacopacabana.bo',
        'nit_personeria': 'Personería 145/2012',
        'texto_recibo': 'El agua es un derecho humano. Cuídela.',
        'dia_facturacion': 1,
        'dia_vencimiento_default': 20
    }, follow=True)

    assert response.status_code == 200
    
    # Comprobar actualización en DB
    inst = Institucion.get_solo()
    assert inst.nombre == 'Comité de Agua Potable y Alcantarillado Villa Copacabana'
    assert inst.telefono == '71554433'
    assert inst.dia_vencimiento_default == 20

    # Comprobar registro de auditoría
    assert BitacoraAuditoria.objects.filter(
        modulo='INSTITUCION',
        accion='MODIFICAR',
        resultado='EXITO',
        usuario=usuario_admin
    ).exists()

