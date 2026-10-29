from django.urls import path
from . import views

app_name = 'medidores'

urlpatterns = [
    path('medidores/', views.medidores_list, name='medidores_list'),
    path('medidores/crear/', views.medidor_crear, name='medidor_crear'),
    path('medidores/<int:pk>/editar/', views.medidor_editar, name='medidor_editar'),
    path('medidores/<int:pk>/asignar/', views.medidor_asignar, name='medidor_asignar'),
    path('medidores/asignaciones/<int:pk>/retirar/', views.asignacion_retirar, name='asignacion_retirar'),
]
