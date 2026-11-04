from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from usuarios.views import TokenView
from catalogo.vistas_web import BienvenidaView


urlpatterns = [
    path('', BienvenidaView.as_view(), name='inicio'),
    path('usuarios/', include('usuarios.urls')),
    path('catalogo/', include('catalogo.urls_web')),
    path('pedidos/', include('pedidos.urls_web')),
    path('api/auth/', include('usuarios.urls_api')),
    path('api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('catalogo.urls')),
    path('api/', include('usuarios.urls_direcciones')),
    path('api/', include('pedidos.urls')),
    path('api/auth/token/', TokenView.as_view(), name='api-token'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
