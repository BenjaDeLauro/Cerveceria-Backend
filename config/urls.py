from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from usuarios.views import TokenView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('catalogo.urls')),
    path('api/', include('usuarios.urls')),
    path('api/', include('pedidos.urls')),
    path('api/auth/token/', TokenView.as_view(), name='api-token'),
    path('api-auth/', include('rest_framework.urls')),
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
