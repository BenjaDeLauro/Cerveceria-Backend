from rest_framework.routers import SimpleRouter

from .views import DireccionEnvioViewSet

app_name = "usuarios_api"

router = SimpleRouter()
router.register(
    "direcciones",
    DireccionEnvioViewSet,
    basename="direccion",
)

urlpatterns = router.urls
