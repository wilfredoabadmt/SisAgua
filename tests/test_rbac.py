import pytest
from django.urls import reverse
from apps.core.models import BitacoraAuditoria

@pytest.mark.django_db
def test_cajero_bloqueado_en_roles_y_usuarios(client, usuario_cajero):
    """
    Verifica que un usuario con rol Cajero sea denegado al intentar ver o editar roles (US3, FR-007).
    """
    client.force_login(usuario_cajero)
    
    # Intentar acceder a la lista de roles
    res_roles = client.get(reverse('seguridad:roles_list'))
    # La vista de roles_list verifica permisos en el servidor y responde 403
    assert res_roles.status_code == 403
    
    # Intentar acceder a la lista de usuarios
    res_usuarios = client.get(reverse('seguridad:usuarios_list'))
    assert res_usuarios.status_code == 403

@pytest.mark.django_db
def test_admin_accede_a_roles_exitosamente(client, usuario_admin):
    """
    Verifica que el Administrador con permiso de 'ver' en 'roles' accede sin problemas (US3).
    """
    client.force_login(usuario_admin)
    response = client.get(reverse('seguridad:roles_list'))
    assert response.status_code == 200
    assert "Roles y Matriz de Permisos" in response.content.decode('utf-8')
