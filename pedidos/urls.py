from rest_framework.routers import SimpleRouter

from .views import PedidoViewSet, DetallePedidoViewSet

app_name = "pedidos_api"

router = SimpleRouter()
router.register("pedidos", PedidoViewSet, basename="pedido")
router.register(
    "detalles-pedido",
    DetallePedidoViewSet,
    basename="detalle-pedido",
)

urlpatterns = router.urls