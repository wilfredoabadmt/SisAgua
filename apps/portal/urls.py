from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.portal_dashboard, name='dashboard'),
    path('medidores/', views.portal_medidores, name='medidores'),
    path('deudas/', views.portal_deudas, name='deudas'),
    path('recibos/', views.portal_recibos, name='recibos'),
    path('recibo/<int:recibo_id>/', views.portal_recibo_detalle, name='recibo_detalle'),
    path('proforma/<str:periodo>/', views.portal_proforma, name='proforma'),
    path('perfil/', views.portal_perfil, name='perfil'),
]

