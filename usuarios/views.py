from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import DireccionEnvio
from .serializers import DireccionEnvioSerializer


class DireccionEnvioViewSet(viewsets.ModelViewSet):
    serializer_class = DireccionEnvioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DireccionEnvio.objects.filter(
            usuario=self.request.user
        ).order_by("id")

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(
                "No se puede eliminar una dirección utilizada en pedidos."
            )