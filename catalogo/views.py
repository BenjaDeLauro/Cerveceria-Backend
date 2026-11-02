from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .models import Categoria, Marca, Producto, Presentacion, Proveedor
from .permissions import IsStaffOrReadOnly
from .serializers import (
    CategoriaSerializer,
    MarcaSerializer,
    ProductoSerializer,
    ProductoPublicSerializer,
    PresentacionSerializer,
    ProveedorSerializer,
)


# ModelViewSet de producto: contiene metodos GET,PUT,PATCH y DELETE
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related(
        "categoria", "marca"
    ).order_by("id")
    serializer_class = ProductoSerializer
    permission_classes = [IsStaffOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]
    filterset_fields = ["categoria", "marca", "presentacion"]
    search_fields = ["nombre", "descripcion"]


    def get_serializer_class(self):
        if self.action == "list":
            return ProductoPublicSerializer
        return ProductoSerializer

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede eliminar un producto incluido en pedidos."
            )


# ModelViewSet de categoría.
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.order_by("id")
    serializer_class = CategoriaSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede eliminar una categoría con productos asociados."
            )


# ModelViewSet de marca.
class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.order_by("id")
    serializer_class = MarcaSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede eliminar una marca con productos asociados."
            )


# ModelViewSet de presentación.
class PresentacionViewSet(viewsets.ModelViewSet):
    queryset = Presentacion.objects.order_by("nombre", "capacidad_ml", "id")
    serializer_class = PresentacionSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede eliminar una presentación con productos asociados."
            )


# ModelViewSet de proveedor.
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.order_by("nombre", "id")
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminUser]