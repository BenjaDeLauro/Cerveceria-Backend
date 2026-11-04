from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogo.models import Categoria, Marca, Presentacion, Producto


class Command(BaseCommand):
    help = 'Carga tres productos de demostración y completa sus imágenes faltantes.'

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
        imagenes_cargadas = 0
        carpeta_imagenes = Path(__file__).resolve().parents[2] / 'demo_images'
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
            creados += int(nuevo)
            if not producto.imagen:
                imagen = carpeta_imagenes / f'imperiosur-{estilo.lower()}.png'
                with imagen.open('rb') as archivo:
                    producto.imagen.save(imagen.name, File(archivo), save=True)
                imagenes_cargadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'{creados} productos demo creados. {imagenes_cargadas} imágenes cargadas.'
        ))
