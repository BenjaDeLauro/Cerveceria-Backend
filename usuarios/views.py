from django.db.models.deletion import ProtectedError
from rest_framework import viewsets, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.views import ObtainAuthToken
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import extend_schema, inline_serializer


from .models import DireccionEnvio
from .serializers import DireccionEnvioSerializer


class DireccionEnvioViewSet(viewsets.ModelViewSet):
    serializer_class = DireccionEnvioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DireccionEnvio.objects.none()

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

class TokenView(ObtainAuthToken):
    schema = AutoSchema()

    @extend_schema(
        summary="Obtener un token con usuario y contraseña",
        responses=inline_serializer(
            name="TokenResponse",
            fields={"token": serializers.CharField()},
        ),
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)