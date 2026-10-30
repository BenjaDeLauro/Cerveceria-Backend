from django.urls import path

from .views import (
    ProductosListCreateAPIView,
    ProductoDetailAPIView,
    CategoriaListCreateAPIView,
    CategoriaDetailAPIView,
    MarcaListCreateAPIView,
    MarcaDetailAPIView,
)

app_name = "catalogo_api"

urlpatterns = [
    path("productos/", ProductosListCreateAPIView.as_view(), name="producto-list"),
    path("productos/<int:pk>/", ProductoDetailAPIView.as_view(), name="producto-detail"),
    path("categorias/", CategoriaListCreateAPIView.as_view(), name="categoria-list"),
    path("categorias/<int:pk>/", CategoriaDetailAPIView.as_view(), name="categoria-detail"),
    path("marcas/", MarcaListCreateAPIView.as_view(), name="marca-list"),
    path("marcas/<int:pk>/", MarcaDetailAPIView.as_view(), name="marca-detail"),
]
