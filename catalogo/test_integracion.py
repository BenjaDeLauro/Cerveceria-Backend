from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import override_settings
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Categoria, Marca, Producto


class IntegracionFrontendTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre='Cervezas')
        cls.marca = Marca.objects.create(nombre='Marca de prueba')
        cls.producto = Producto.objects.create(nombre='IPA', categoria=cls.categoria, marca=cls.marca, precio=2500, stock=8)

    def test_busqueda_y_categoria_se_combinan_antes_de_paginar(self):
        otra = Categoria.objects.create(nombre='Oscuras')
        Producto.objects.create(nombre='IPA oscura', categoria=otra, marca=self.marca, precio=3000)
        respuesta = self.client.get('/api/productos/', {'search': 'IPA', 'categoria': self.categoria.pk})
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['id'], self.producto.pk)
        self.assertEqual(self.client.get('/api/productos/?search=inexistente').data['count'], 0)
        self.assertEqual(self.client.get('/api/productos/?categoria=incorrecta').status_code, 400)

    def test_paginacion_conserva_busqueda_y_categoria(self):
        for numero in range(7):
            Producto.objects.create(nombre=f'IPA {numero}', categoria=self.categoria, marca=self.marca, precio=3000)
        respuesta = self.client.get('/api/productos/', {'search': 'IPA', 'categoria': self.categoria.pk})
        self.assertEqual(respuesta.data['count'], 8)
        self.assertEqual(len(respuesta.data['results']), 6)
        siguiente = self.client.get(respuesta.data['next'])
        self.assertEqual(len(siguiente.data['results']), 2)
        self.assertIsNone(siguiente.data['next'])

    def test_cors_acepta_front_local_y_rechaza_otro_origen(self):
        respuesta = self.client.get('/api/productos/', HTTP_ORIGIN='http://127.0.0.1:3000')
        self.assertEqual(respuesta['Access-Control-Allow-Origin'], 'http://127.0.0.1:3000')
        respuesta = self.client.get('/api/productos/', HTTP_ORIGIN='https://ajeno.example')
        self.assertNotIn('Access-Control-Allow-Origin', respuesta)

    def test_token_staff_y_revocacion_en_api_integrada(self):
        from django.contrib.auth import get_user_model
        staff = get_user_model().objects.create_user(username='integrador', is_staff=True)
        token = Token.objects.create(user=staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        self.assertEqual(self.client.patch(f'/api/productos/{self.producto.pk}/', {'stock': 9}).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 204)
        self.assertIn(self.client.patch(f'/api/productos/{self.producto.pk}/', {'stock': 10}).status_code, (401, 403))

    def test_demo_no_modifica_productos_existentes(self):
        with TemporaryDirectory() as carpeta, override_settings(BASE_DIR=Path(carpeta)):
            call_command('cargar_catalogo_demo', verbosity=0)
            demo = Producto.objects.get(nombre='ImperioSur IPA')
            demo.stock = 25
            demo.save()
            call_command('cargar_catalogo_demo', verbosity=0)
            demo.refresh_from_db()
            self.assertEqual(demo.stock, 25)
            self.assertEqual(Producto.objects.filter(nombre__startswith='ImperioSur ').count(), 3)
