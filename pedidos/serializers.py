from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from catalogo.models import Producto

from .models import Pedido, DetallePedido


class DetallePedidoSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = DetallePedido
        fields = [
            "id",
            "pedido",
            "producto",
            "cantidad",
            "precio_unitario",
            "subtotal",
        ]


class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = [
            "id",
            "usuario",
            "fecha",
            "estado",
            "direccion_envio",
        ]
        read_only_fields = ["usuario", "fecha", "estado"]

    def validate_direccion_envio(self, direccion):
        usuario = self.context["request"].user

        if direccion is not None and direccion.usuario_id != usuario.id:
            raise serializers.ValidationError(
                "La dirección debe pertenecer al usuario autenticado."
            )

        return direccion


class PedidoListSerializer(PedidoSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)

    class Meta(PedidoSerializer.Meta):
        fields = PedidoSerializer.Meta.fields + ["detalles"]


class RenglonCompraSerializer(serializers.Serializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())
    cantidad = serializers.IntegerField(min_value=1, max_value=2147483647)


class PedidoCompraSerializer(PedidoSerializer):
    items = RenglonCompraSerializer(many=True, allow_empty=False, write_only=True)

    class Meta(PedidoSerializer.Meta):
        fields = PedidoSerializer.Meta.fields + ["items"]

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        ids = [item["producto"].pk for item in items]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({"items": "Ingresá cada producto una sola vez."})

        detalles = []
        for item in sorted(items, key=lambda item: item["producto"].pk):
            producto = item["producto"]
            cantidad = item["cantidad"]
            disponibles = Producto.objects.filter(pk=producto.pk, stock__gte=cantidad)
            if not disponibles.update(stock=F("stock") - cantidad):
                raise serializers.ValidationError({
                    "items": f"Stock insuficiente para {producto.nombre}.",
                })
            producto.refresh_from_db(fields=["precio"])
            detalles.append(DetallePedido(
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
            ))

        pedido = super().create({**validated_data, "stock_descontado": True})
        for detalle in detalles:
            detalle.pedido = pedido
        DetallePedido.objects.bulk_create(detalles)
        return pedido


class PedidoTotalSerializer(serializers.Serializer):
    pedido = serializers.IntegerField()
    total = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
    )
