import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class ConfiguracionEntornoTests(SimpleTestCase):
    def leer_configuracion(self, **variables):
        entorno = os.environ.copy()
        for nombre in ('DJANGO_SECRET_KEY', 'DJANGO_DEBUG', 'DJANGO_ALLOWED_HOSTS',
                       'DJANGO_DATA_DIR', 'DJANGO_MEDIA_ROOT'):
            entorno.pop(nombre, None)
        entorno.update(variables)
        resultado = subprocess.run(
            [sys.executable, '-c', (
                'import json; from config import settings as s; '
                'print(json.dumps({"debug": s.DEBUG, "hosts": s.ALLOWED_HOSTS, '
                '"base": str(s.BASE_DIR), "db": str(s.DATABASES["default"]["NAME"]), '
                '"media": str(s.MEDIA_ROOT), "clave": s.SECRET_KEY}))'
            )],
            cwd=Path(__file__).resolve().parent.parent,
            env=entorno, capture_output=True, text=True, check=True,
        )
        return json.loads(resultado.stdout)

    def test_ejecucion_nativa_conserva_rutas_y_debug_locales(self):
        configuracion = self.leer_configuracion()
        base = Path(configuracion['base'])
        self.assertIs(configuracion['debug'], True)
        self.assertEqual(Path(configuracion['db']), base / 'db.sqlite3')
        self.assertEqual(Path(configuracion['media']), base / 'media')
        self.assertIn('127.0.0.1', configuracion['hosts'])

    def test_entorno_puede_separar_datos_media_hosts_y_desactivar_debug(self):
        with TemporaryDirectory() as temporal:
            datos, media = Path(temporal) / 'datos', Path(temporal) / 'imagenes'
            configuracion = self.leer_configuracion(
                DJANGO_DATA_DIR=str(datos), DJANGO_MEDIA_ROOT=str(media),
                DJANGO_DEBUG='false', DJANGO_SECRET_KEY='clave-solo-de-prueba',
                DJANGO_ALLOWED_HOSTS=' localhost, ejemplo.test, ,',
            )
        self.assertIs(configuracion['debug'], False)
        self.assertEqual(Path(configuracion['db']), datos / 'db.sqlite3')
        self.assertEqual(Path(configuracion['media']), media)
        self.assertEqual(configuracion['hosts'], ['localhost', 'ejemplo.test'])
        self.assertEqual(configuracion['clave'], 'clave-solo-de-prueba')
