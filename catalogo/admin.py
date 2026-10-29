from django.contrib import admin
from .models import Categoria, Marca, Producto


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
    list_display = ('id', 'nombre', 'categoria', 'marca', 'precio', 'stock')
    list_filter = ('categoria', 'marca')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)