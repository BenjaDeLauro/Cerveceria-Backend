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


from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import IngresoForm, RegistroForm
from .roles import GRUPO_CLIENTES


class RegistroView(CreateView):
    form_class = RegistroForm
    template_name = 'usuarios/registro.html'
    success_url = reverse_lazy('inicio')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('inicio')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            grupo, _ = Group.objects.get_or_create(name=GRUPO_CLIENTES)
            self.object.groups.add(grupo)
        login(self.request, self.object)
        messages.success(self.request, 'Tu cuenta está lista. ¡Bienvenido!')
        return redirect(self.success_url)


class IngresoView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = IngresoForm
    redirect_authenticated_user = True


class SalidaView(LogoutView):
    # Django solo admite POST y exige CSRF para cerrar la sesión.
    next_page = reverse_lazy('inicio')
