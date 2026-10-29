from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    # Catálogo de Servicios
    path('servicios/', views.servicios_list, name='servicios_list'),
    path('servicios/crear/', views.servicio_crear, name='servicio_crear'),
    path('servicios/<int:pk>/editar/', views.servicio_editar, name='servicio_editar'),

    # Tarifarios y Tramos
    path('servicios/tarifarios/', views.tarifarios_list, name='tarifarios_list'),
    path('servicios/tarifarios/crear/', views.tarifario_crear, name='tarifario_crear'),
    path('servicios/tarifarios/<int:pk>/', views.tarifario_detalle, name='tarifario_detalle'),
    path('servicios/tarifarios/<int:pk>/tramos/crear/', views.tramo_crear, name='tramo_crear'),
]
