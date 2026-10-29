import pytest
from django.urls import reverse
from apps.core.models import BitacoraAuditoria
from apps.core.services import registrar_auditoria

@pytest.mark.django_db
def test_auditor_o_admin_accede_a_auditoria(client, usuario_admin):
    """
    Verifica que el usuario con permiso 'ver' en 'institucion' puede consultar la bitácora (US7).
    """
    client.force_login(usuario_admin)
    registrar_auditoria(modulo="SOCIOS", accion="CREAR", resultado="EXITO")

    response = client.get(reverse('core:auditoria_list'))
    assert response.status_code == 200
    assert "Pista de Auditoría Inalterable" in response.content.decode('utf-8')
    assert "SOCIOS:CREAR" in response.content.decode('utf-8')


@pytest.mark.django_db
def test_filtro_por_modulo_en_auditoria(client, usuario_admin):
    """
    Verifica el filtrado de eventos en la bitácora por módulo (US7).
    """
    client.force_login(usuario_admin)
    registrar_auditoria(modulo="CAJA", accion="COBRAR", resultado="EXITO")
    registrar_auditoria(modulo="LECTURAS", accion="CREAR", resultado="EXITO")

    response = client.get(reverse('core:auditoria_list') + '?modulo=CAJA')
    assert response.status_code == 200
    contenido = response.content.decode('utf-8')
    assert "CAJA:COBRAR" in contenido
    assert "LECTURAS:CREAR" not in contenido

