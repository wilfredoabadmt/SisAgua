from django.urls import path
from . import views

app_name = 'transcripcion'

urlpatterns = [
    path('lotes/', views.lotes_list, name='lotes_list'),
    path('lotes/crear/', views.lote_crear, name='lote_crear'),
    path('lotes/<int:pk>/', views.lote_detalle, name='lote_detalle'),
    path('lotes/<int:lote_id>/capturar/', views.transcripcion_capturar, name='transcripcion_capturar'),
    path('registros/<int:pk>/validar/', views.transcripcion_validar_view, name='transcripcion_validar'),
    path('registros/<int:pk>/observar/', views.transcripcion_observar_view, name='transcripcion_observar'),
    path('registros/<int:pk>/rechazar/', views.transcripcion_rechazar_view, name='transcripcion_rechazar'),
    path('registros/<int:pk>/regularizar/', views.transcripcion_regularizar_view, name='transcripcion_regularizar'),
    path('reporte/', views.reporte_transcripcion_view, name='reporte_transcripcion'),
]

