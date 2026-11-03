from decimal import Decimal

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import Categoria, Marca, Presentacion, Producto


class Command(BaseCommand):
    help = 'Agrega tres productos de demostración sin sobrescribir datos existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        marca, _ = Marca.objects.get_or_create(nombre='ImperioSur')
        presentacion, _ = Presentacion.objects.get_or_create(nombre='Botella', capacidad_ml=500)
        estilos = [
            ('IPA', 'Lupuladas', '3200.00', 12, 'Aromática y de amargor marcado.'),
            ('Golden', 'Rubias', '2800.00', 18, 'Dorada, suave y refrescante.'),
            ('Stout', 'Oscuras', '3400.00', 8, 'Oscura, con notas de maltas tostadas.'),
        ]
        creados = 0
        for estilo, categoria_nombre, precio, stock, descripcion in estilos:
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
            producto, nuevo = Producto.objects.get_or_create(
                nombre=f'ImperioSur {estilo}', marca=marca,
                defaults={
                    'categoria': categoria, 'presentacion': presentacion,
                    'descripcion': f'{descripcion} Registro de demostración para la EFI: precio y stock de prueba.',
                    'precio': Decimal(precio), 'stock': stock,
                },
            )
            if nuevo:
                imagen = settings.BASE_DIR.parent / 'ImperioSur-Frontend' / 'public' / 'images' / f'imperiosur-{estilo.lower()}.png'
                if imagen.is_file():
                    with imagen.open('rb') as archivo:
                        producto.imagen.save(imagen.name, File(archivo), save=True)
                creados += 1
        self.stdout.write(self.style.SUCCESS(f'{creados} productos demo creados. Los existentes se conservaron.'))
