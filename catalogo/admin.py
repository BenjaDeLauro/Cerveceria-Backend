from django.contrib import admin
from .models import Categoria, Marca, Presentacion, Producto, Proveedor, Resena


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'categoria', 'marca', 'presentacion', 'precio', 'stock')
    list_filter = ('categoria', 'marca', 'presentacion', 'proveedores')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    list_select_related = ('categoria', 'marca', 'presentacion')
    filter_horizontal = ('proveedores',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'proveedores':
            kwargs['help_text'] = (
                'Si la lista está vacía, creá un proveedor con el botón +. '
                'Pasá los proveedores elegidos a la lista de seleccionados y guardá el producto.'
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(Presentacion)
class PresentacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'capacidad_ml')
    list_filter = ('capacidad_ml',)
    search_fields = ('nombre',)
    ordering = ('nombre', 'capacidad_ml')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'email', 'telefono', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'email', 'telefono')
    ordering = ('nombre',)


@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'usuario', 'calificacion', 'fecha')
    list_filter = ('calificacion', 'fecha')
    search_fields = ('producto__nombre', 'usuario__username', 'comentario')
    ordering = ('-fecha', '-pk')
    list_select_related = ('producto', 'usuario')
    autocomplete_fields = ('producto', 'usuario')
    readonly_fields = ('fecha',)
