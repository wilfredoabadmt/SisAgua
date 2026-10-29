from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    path('configuracion/institucion/', views.institucion_config_view, name='institucion_config'),
    path('administracion/menus/', views.menus_list_view, name='menus_list'),
]

