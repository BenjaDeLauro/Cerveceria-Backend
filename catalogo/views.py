from django.db.models.deletion import ProtectedError
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Categoria, Marca, Producto
from .permissions import IsStaffOrReadOnly
from .serializers import (
    CategoriaSerializer,
    MarcaSerializer,
    ProductoSerializer,
    ProductoPublicSerializer,
)


# GET lista productos; POST crea un producto.
class ProductosListCreateAPIView(generics.ListCreateAPIView):
    queryset = Producto.objects.all().select_related("categoria", "marca")
    permission_classes = [IsStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductoPublicSerializer
        return ProductoSerializer


# GET obtiene un producto; PUT/PATCH modifican; DELETE elimina.
class ProductoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.all().select_related("categoria", "marca")
    permission_classes = [IsStaffOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ProductoPublicSerializer
        return ProductoSerializer

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("No se puede eliminar un producto incluido en pedidos.")


# GET lista categorías; POST crea una categoría.
class CategoriaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsStaffOrReadOnly]


# GET, PUT, PATCH y DELETE de una categoría.
class CategoriaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("No se puede eliminar una categoría con productos asociados.")


# GET lista marcas; POST crea una marca.
class MarcaListCreateAPIView(generics.ListCreateAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsStaffOrReadOnly]


# GET, PUT, PATCH y DELETE de una marca.
class MarcaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError("No se puede eliminar una marca con productos asociados.")
