"""
URL configuration for SisAgua project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # SisAgua Core y Seguridad
    path('', include('apps.seguridad.urls')),
    path('', include('apps.configuracion.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.socios.urls')),
    path('', include('apps.servicios.urls')),
    path('', include('apps.medidores.urls')),
    path('', include('apps.consumo.urls')),
    path('', include('apps.caja.urls')),
    path('transcripcion/', include('apps.transcripcion.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('portal/', include('apps.portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

