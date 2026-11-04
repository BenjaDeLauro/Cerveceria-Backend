from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.db.models import F
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from catalogo.models import Producto


class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )

    fecha = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='pendiente'
    )

    direccion_envio = models.ForeignKey(
        'usuarios.DireccionEnvio',
        on_delete=models.PROTECT,
        related_name='pedidos',
        blank=True,
        null=True,
    )

    stock_descontado = models.BooleanField(default=False, editable=False)

    @transaction.atomic
    def cancelar(self, *, permitir_confirmado=False):
        estados = ['pendiente', 'confirmado'] if permitir_confirmado else ['pendiente']
        actualizados = Pedido.objects.filter(pk=self.pk, estado__in=estados).update(
            estado='cancelado',
        )
        if not actualizados:
            return False

        if self.stock_descontado:
            for detalle in self.detalles.order_by('producto_id'):
                Producto.objects.filter(pk=detalle.producto_id).update(
                    stock=F('stock') + detalle.cantidad,
                )
        self.estado = 'cancelado'
        return True

    def clean(self):
        super().clean()
        if self.direccion_envio_id and self.usuario_id:
            try:
                direccion = self.direccion_envio
            except ObjectDoesNotExist:
                # La validación del ForeignKey informa la dirección inexistente.
                return
            if direccion.usuario_id != self.usuario_id:
                raise ValidationError({
                    'direccion_envio': 'La dirección debe pertenecer al usuario del pedido.',
                })

    def __str__(self):
        return f'Pedido #{self.id} - {self.usuario.username}'


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        'catalogo.Producto',
        on_delete=models.PROTECT,
        related_name='detalles_pedido'
    )

    cantidad = models.PositiveIntegerField()

    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f'{self.producto.nombre} x {self.cantidad}'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


@receiver(pre_delete, sender=Pedido)
def liberar_stock_al_eliminar_pedido(sender, instance, **kwargs):
    if instance.stock_descontado:
        instance.cancelar()
