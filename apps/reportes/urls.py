from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('deudores/', views.reporte_deudores, name='deudores'),
    path('recaudacion/', views.reporte_recaudacion, name='recaudacion'),
    path('consumo/', views.reporte_consumo, name='consumo'),
    path('zonas/', views.reporte_zonas, name='zonas'),
    path('membresias/', views.reporte_membresias, name='membresias'),
    path('socio/<int:socio_id>/', views.reporte_socio_estado_cuenta, name='socio_estado_cuenta'),
]

