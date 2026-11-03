from decimal import Decimal

from django import forms

from .models import Categoria, Producto


class ProductoForm(forms.ModelForm):
    precio = forms.DecimalField(label='Precio', min_value=Decimal('0.01'),
                                max_digits=10, decimal_places=2)

    class Meta:
        model = Producto
        fields = ('nombre', 'descripcion', 'precio', 'stock', 'imagen',
                  'categoria', 'marca', 'presentacion', 'proveedores')
        labels = {'descripcion': 'Descripción', 'presentacion': 'Presentación',
                  'categoria': 'Categoría'}
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        labels = {'descripcion': 'Descripción'}
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}
