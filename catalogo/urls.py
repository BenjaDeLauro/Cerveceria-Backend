from rest_framework.routers import SimpleRouter

from .views import (
    CategoriaViewSet,
    MarcaViewSet,
    ProductoViewSet,
    PresentacionViewSet,
    ProveedorViewSet,
)

app_name = "catalogo_api"

router = SimpleRouter()

router.register("productos", ProductoViewSet, basename="producto")
router.register("categorias", CategoriaViewSet, basename="categoria")
router.register("marcas", MarcaViewSet, basename="marca")
router.register("presentaciones", PresentacionViewSet, basename="presentacion")
router.register("proveedores", ProveedorViewSet, basename="proveedor")

urlpatterns = router.urls
