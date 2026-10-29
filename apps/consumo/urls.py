from django.urls import path
from . import views

app_name = 'consumo'

urlpatterns = [
    # Lecturas de Consumo
    path('consumo/lecturas/', views.lecturas_list, name='lecturas_list'),
    path('consumo/lecturas/capturar/', views.lectura_capturar, name='lectura_capturar'),
    path('consumo/lecturas/<int:pk>/corregir/', views.lectura_corregir, name='lectura_corregir'),
    path('consumo/observadas/', views.observadas_list, name='observadas_list'),
    path('consumo/proformas/<int:pk>/', views.proforma_detalle, name='proforma_detalle'),

    # Facturación Mensual Idempotente
    path('consumo/facturacion/', views.facturacion_panel, name='facturacion_panel'),
    path('consumo/facturacion/ejecutar/', views.facturacion_ejecutar, name='facturacion_ejecutar'),
]

