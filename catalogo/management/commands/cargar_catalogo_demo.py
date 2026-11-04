from decimal import Decimal
from hashlib import file_digest
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalogo.models import Categoria, Marca, Presentacion, Producto


# Identifica las fotos demo que se publicaron con fondo negro.
FOTOS_DEMO_ANTERIORES = {
    'imperiosur-honey.png': '7f8242a15b15145b4a9ccdfc91b822d4ee5493a6564cc307ec824e8a5661a339',
    'imperiosur-porter.png': '83e42246ed1a293efbbb3126b2a3c64a143840c30b77afbf8b8aa6602b1eef67',
    'imperiosur-red-ale.png': 'bdd65843632690a1016c5a595d3b93600915a3faa2c5455350befaaa5cbc969e',
}


def es_foto_demo_anterior(imagen, nombre_demo):
    huella_anterior = FOTOS_DEMO_ANTERIORES.get(nombre_demo)
    if not huella_anterior:
        return False
    try:
        with imagen.open('rb') as archivo:
            return file_digest(archivo, 'sha256').hexdigest() == huella_anterior
    except FileNotFoundError:
        return False


class Command(BaseCommand):
    help = 'Carga seis productos de demostración y completa o actualiza sus fotos de muestra.'

    @transaction.atomic
    def handle(self, *args, **options):
        marca, _ = Marca.objects.get_or_create(nombre='ImperioSur')
        presentacion, _ = Presentacion.objects.get_or_create(nombre='Botella', capacidad_ml=500)
        estilos = [
            ('IPA', 'Lupuladas', '3200.00', 12, 'Aromática y de amargor marcado.'),
            ('Golden', 'Rubias', '2800.00', 18, 'Dorada, suave y refrescante.'),
            ('Stout', 'Oscuras', '3400.00', 8, 'Oscura, con notas de maltas tostadas.'),
            ('Red Ale', 'Rojas', '3100.00', 14, 'Cobriza, con notas de caramelo y malta tostada.'),
            ('Honey', 'Rubias', '3000.00', 16, 'Dorada, con aroma a miel y final suave.'),
            ('Porter', 'Oscuras', '3500.00', 10, 'Oscura, con notas de chocolate y un tostado suave.'),
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
            imagen = carpeta_imagenes / f'imperiosur-{slugify(estilo)}.png'
            if not producto.imagen or es_foto_demo_anterior(producto.imagen, imagen.name):
                with imagen.open('rb') as archivo:
                    producto.imagen.save(imagen.name, File(archivo), save=False)
                producto.save(update_fields=['imagen'])
                imagenes_cargadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'{creados} productos demo creados. {imagenes_cargadas} imágenes cargadas.'
        ))
