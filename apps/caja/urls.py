from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('cobros/', views.cobros_ventanilla, name='cobros'),
    path('cobros/procesar/', views.procesar_cobro_view, name='procesar_cobro'),
    path('recibos/', views.recibos_list, name='recibos_list'),
    path('recibos/<int:pk>/', views.recibo_detalle, name='recibo_detalle'),
    path('recibos/<int:pk>/anular/', views.recibo_anular_view, name='recibo_anular'),
    path('turnos/', views.turnos_list, name='turnos_list'),
    path('turnos/apertura/', views.turno_apertura, name='turno_apertura'),
    path('turnos/cierre/', views.turno_cierre, name='turno_cierre'),
]

