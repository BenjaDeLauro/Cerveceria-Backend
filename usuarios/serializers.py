from rest_framework import serializers

from .models import DireccionEnvio


class DireccionEnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionEnvio
        fields = "__all__"
        read_only_fields = ["usuario"]