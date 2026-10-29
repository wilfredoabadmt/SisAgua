import pytest
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.socios.models import Zona, Socio
from apps.core.models import BitacoraAuditoria

@pytest.mark.django_db
def test_admin_puede_listar_zonas(client, usuario_admin):
    client.force_login(usuario_admin)
    Zona.objects.create(codigo="CENTRO", nombre="Zona Central")
    res = client.get(reverse('socios:zonas_list'))
    assert res.status_code == 200
    assert "Zona Central" in res.content.decode()

@pytest.mark.django_db
def test_usuario_sin_permiso_recibe_403(client, usuario_cajero):
    client.force_login(usuario_cajero)
    res = client.get(reverse('socios:zonas_list'))
    assert res.status_code == 403

@pytest.mark.django_db
def test_crear_zona_exitosamente_y_auditoria(client, usuario_admin):
    client.force_login(usuario_admin)
    data = {
        'codigo': 'norte-1',  # Debe normalizarse a mayúsculas
        'nombre': 'Sector Norte Alto',
        'descripcion': 'Límite con la represa',
        'responsable': 'Don Pedro Quispe',
        'observaciones': 'Acceso vehicular difícil'
    }
    res = client.post(reverse('socios:zona_crear'), data=data)
    assert res.status_code == 302
    
    zona = Zona.objects.get(codigo='NORTE-1')
    assert zona.nombre == 'Sector Norte Alto'
    assert zona.activo is True

    # Verificar auditoría
    audit = BitacoraAuditoria.objects.filter(modulo='ZONAS', accion='CREAR').latest('fecha_hora_utc')
    assert audit.usuario == usuario_admin
    assert audit.resultado == 'EXITO'

@pytest.mark.django_db
def test_rechazo_de_codigo_de_zona_duplicado(client, usuario_admin):
    client.force_login(usuario_admin)
    Zona.objects.create(codigo="SUR", nombre="Zona Sur 1")
    data = {
        'codigo': 'SUR',
        'nombre': 'Zona Sur Duplicada'
    }
    res = client.post(reverse('socios:zona_crear'), data=data)
    assert res.status_code == 200  # Re-renders form with error
    assert Zona.objects.filter(codigo="SUR").count() == 1

@pytest.mark.django_db
def test_editar_zona_exitosamente(client, usuario_admin):
    client.force_login(usuario_admin)
    zona = Zona.objects.create(codigo="ESTE", nombre="Zona Este")
    data = {
        'codigo': 'ESTE',
        'nombre': 'Zona Este Modificada',
        'responsable': 'Doña Rosa'
    }
    res = client.post(reverse('socios:zona_editar', kwargs={'pk': zona.pk}), data=data)
    assert res.status_code == 302
    zona.refresh_from_db()
    assert zona.nombre == 'Zona Este Modificada'
    assert zona.responsable == 'Doña Rosa'

@pytest.mark.django_db
def test_bloqueo_de_borrado_fisico_en_zona_con_socios(db):
    zona = Zona.objects.create(codigo="OESTE", nombre="Zona Oeste")
    Socio.objects.create(
        codigo="SOC-TEST-1",
        ci="1234567",
        nombres="Juan",
        apellidos="Pérez",
        zona=zona,
        direccion="Calle 1"
    )
    with pytest.raises(ValidationError) as exc_info:
        zona.delete()
    assert "No se permite eliminar físicamente" in str(exc_info.value)

@pytest.mark.django_db
def test_desactivar_zona_logicamente(client, usuario_admin):
    client.force_login(usuario_admin)
    zona = Zona.objects.create(codigo="TEMP", nombre="Zona Temporal", activo=True)
    res = client.post(reverse('socios:zona_desactivar', kwargs={'pk': zona.pk}))
    assert res.status_code == 302
    zona.refresh_from_db()
    assert zona.activo is False

