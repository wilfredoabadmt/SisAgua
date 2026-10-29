from django.urls import path
from . import views

app_name = 'seguridad'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfil/cambiar-contrasena/', views.cambiar_contrasena_view, name='cambiar_contrasena'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('administracion/roles/', views.roles_list_view, name='roles_list'),
    path('administracion/usuarios/', views.usuarios_list_view, name='usuarios_list'),
    path('administracion/usuarios/ficha-enrolamiento/', views.ficha_enrolamiento_view, name='ficha_enrolamiento'),
    path('administracion/usuarios/sugerir-username/', views.sugerir_username_view, name='sugerir_username'),
]
