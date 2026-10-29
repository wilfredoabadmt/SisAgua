from django.urls import path
from . import views

app_name = 'socios'

urlpatterns = [
    # Zonas
    path('zonas/', views.zonas_list, name='zonas_list'),
    path('zonas/crear/', views.zona_crear, name='zona_crear'),
    path('zonas/<int:pk>/editar/', views.zona_editar, name='zona_editar'),
    path('zonas/<int:pk>/desactivar/', views.zona_desactivar, name='zona_desactivar'),

    # Socios
    path('socios/', views.socios_list, name='socios_list'),
    path('socios/crear/', views.socio_crear, name='socio_crear'),
    path('socios/<int:pk>/', views.socio_detalle, name='socio_detalle'),
    path('socios/<int:pk>/editar/', views.socio_editar, name='socio_editar'),
    path('socios/<int:pk>/estado/', views.socio_cambiar_estado, name='socio_cambiar_estado'),
    path('socios/<int:pk>/habilitar-portal/', views.socio_habilitar_portal, name='socio_habilitar_portal'),
]

