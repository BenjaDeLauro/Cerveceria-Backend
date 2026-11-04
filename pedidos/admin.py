from django.contrib import admin
from django.db.models import F

from .models import Pedido, DetallePedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1

    def has_add_permission(self, request, obj=None):
        return not (obj and obj.stock_descontado) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.stock_descontado) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not (obj and obj.stock_descontado) and super().has_delete_permission(request, obj)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'usuario',
        'fecha',
        'estado',
        'direccion_envio',
    )

    list_filter = ('estado', 'fecha')
    search_fields = ('usuario__username',)
    ordering = ('-fecha',)
    list_select_related = ('usuario', 'direccion_envio')
    autocomplete_fields = ('usuario', 'direccion_envio')

    inlines = [DetallePedidoInline]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.stock_descontado and obj.estado == 'cancelado':
            return ('estado',)
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        if change and obj.stock_descontado:
            # El formulario del admin se guarda en una transacción.
            actual = Pedido.objects.filter(pk=obj.pk)
            actual.update(estado=F('estado'))
            if actual.values_list('estado', flat=True).get() == 'cancelado':
                obj.estado = 'cancelado'
            elif obj.estado == 'cancelado':
                obj.cancelar(permitir_confirmado=True)
        super().save_model(request, obj, form, change)


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pedido',
        'producto',
        'cantidad',
        'precio_unitario',
        'subtotal'
    )

    search_fields = ('producto__nombre',)
    ordering = ('id',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'pedido':
            kwargs['queryset'] = Pedido.objects.filter(stock_descontado=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        return not (obj and obj.pedido.stock_descontado) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Al eliminar el pedido completo, el modelo libera su reserva.
        ruta = request.resolver_match
        desde_detalles = ruta and ruta.url_name.startswith('pedidos_detallepedido_')
        if desde_detalles and obj and obj.pedido.stock_descontado:
            return False
        return super().has_delete_permission(request, obj)
