from rest_framework import serializers

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


class PedidoTotalSerializer(serializers.Serializer):
    pedido = serializers.IntegerField()
    total = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
    )