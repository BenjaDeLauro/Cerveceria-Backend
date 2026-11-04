from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import Pedido, DetallePedido
from .serializers import (
    PedidoSerializer,
    PedidoCompraSerializer,
    PedidoListSerializer,
    DetallePedidoSerializer,
    PedidoTotalSerializer
)


class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Pedido.objects.none()

        return Pedido.objects.filter(
            usuario=self.request.user
        ).prefetch_related("detalles").order_by("-fecha", "-id")

    def get_serializer_class(self):
        if self.action == "list":
            return PedidoListSerializer
        if self.action == "create":
            return PedidoCompraSerializer
        return PedidoSerializer

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        actualizado = self.get_queryset().filter(
            pk=serializer.instance.pk, estado="pendiente",
        ).update(estado="pendiente")
        if not actualizado:
            raise ValidationError(
                "Solo se pueden modificar pedidos pendientes."
            )
        serializer.instance.refresh_from_db()
        serializer.save()

    @transaction.atomic
    def perform_destroy(self, instance):
        if not instance.cancelar():
            raise ValidationError(
                "Solo se pueden eliminar pedidos pendientes."
            )

        instance.delete()

    @extend_schema(
        summary="Consultar el total de un pedido",
        responses=PedidoTotalSerializer,
    )
    @action(detail=True, methods=["get"])
    def total(self, request, pk=None):
        pedido = self.get_object()

        importe = sum(
            (detalle.subtotal for detalle in pedido.detalles.all()),
            Decimal("0.00"),
        )

        return Response({
            "pedido": pedido.id,
            "total": f"{importe:.2f}",
        })

    @extend_schema(
        summary="Cancelar un pedido pendiente",
        request=None,
        responses=PedidoSerializer,
    )
    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        pedido = self.get_object()

        if not pedido.cancelar():
            raise ValidationError(
                "Solo se pueden cancelar pedidos pendientes."
            )

        pedido.refresh_from_db()

        return Response(self.get_serializer(pedido).data)


class DetallePedidoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DetallePedidoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DetallePedido.objects.none()

        return DetallePedido.objects.filter(
            pedido__usuario=self.request.user
        ).order_by("id")
