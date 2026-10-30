from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Categoria, Marca, Producto


class CatalogoAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nombre='Cervezas')
        cls.marca = Marca.objects.create(nombre='Marca de prueba')
        cls.producto = Producto.objects.create(
            nombre='IPA', precio='2500.50', stock=8,
            categoria=cls.categoria, marca=cls.marca,
        )

    def test_listas_publicas(self):
        for recurso, objeto in [
            ('categoria', self.categoria),
            ('marca', self.marca),
            ('producto', self.producto),
        ]:
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(reverse(f'catalogo_api:{recurso}-list'))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(len(respuesta.data), 1)
                self.assertEqual(respuesta.data[0]['id'], objeto.pk)
                self.assertEqual(respuesta.data[0]['nombre'], objeto.nombre)

    def test_detalle_producto(self):
        url = reverse('catalogo_api:producto-detail', args=[self.producto.pk])
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['precio'], '2500.50')
        self.assertEqual(respuesta.data['stock'], 8)
        self.assertEqual(respuesta.data['categoria']['id'], self.categoria.pk)
        self.assertEqual(respuesta.data['marca']['id'], self.marca.pk)
        self.assertIsNone(respuesta.data['imagen'])

    def test_recurso_inexistente(self):
        for recurso in ['categoria', 'marca', 'producto']:
            with self.subTest(recurso=recurso):
                url = reverse(f'catalogo_api:{recurso}-detail', args=[99999])
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_escritura_anonima_rechazada(self):
        for recurso, objeto in [
            ('categoria', self.categoria),
            ('marca', self.marca),
            ('producto', self.producto),
        ]:
            with self.subTest(recurso=recurso):
                lista = reverse(f'catalogo_api:{recurso}-list')
                detalle = reverse(f'catalogo_api:{recurso}-detail', args=[objeto.pk])
                self.assertEqual(self.client.post(lista, {}, format='json').status_code, 403)
                self.assertEqual(self.client.put(detalle, {}, format='json').status_code, 403)
                self.assertEqual(self.client.patch(detalle, {}, format='json').status_code, 403)
                self.assertEqual(self.client.delete(detalle).status_code, 403)
                objeto.refresh_from_db()

    def test_usuario_comun_no_puede_crear(self):
        usuario = get_user_model().objects.create_user(username="cliente")
        self.client.force_authenticate(usuario)
        respuesta = self.client.post(reverse('catalogo_api:producto-list'), {}, format='json')
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_crea_edita_y_elimina_producto(self):
        administrador = get_user_model().objects.create_user(username="admin", is_staff=True)
        self.client.force_authenticate(administrador)
        respuesta = self.client.post(reverse('catalogo_api:producto-list'), {
            'nombre': 'Porter', 'precio': '3000.00', 'stock': 5,
            'categoria': self.categoria.pk, 'marca': self.marca.pk,
        }, format='json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data['categoria'], self.categoria.pk)
        url = reverse('catalogo_api:producto-detail', args=[respuesta.data['id']])
        respuesta = self.client.patch(url, {'precio': '3200.00'}, format='json')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['precio'], '3200.00')
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_relaciones_protegidas(self):
        administrador = get_user_model().objects.create_user(username="admin", is_staff=True)
        self.client.force_authenticate(administrador)
        for recurso, objeto in [('categoria', self.categoria), ('marca', self.marca)]:
            with self.subTest(recurso=recurso):
                url = reverse(f'catalogo_api:{recurso}-detail', args=[objeto.pk])
                self.assertEqual(self.client.delete(url).status_code, 400)
                objeto.refresh_from_db()
