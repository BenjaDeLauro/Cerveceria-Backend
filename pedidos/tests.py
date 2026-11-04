from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from catalogo.models import Categoria, Marca, Producto, Proveedor

from .models import Pedido


class FlujoCompraTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = get_user_model().objects.create_user(username='cliente')
        cls.otro = get_user_model().objects.create_user(username='otro')
        cls.producto = Producto.objects.create(
            nombre='IPA', precio=Decimal('125.50'), stock=3,
            categoria=Categoria.objects.create(nombre='Rubias'),
            marca=Marca.objects.create(nombre='ImperioSur'),
        )

    def test_cliente_pide_desde_catalogo_y_ve_solo_sus_pedidos(self):
        otro_pedido = Pedido.objects.create(usuario=self.otro)
        self.client.force_login(self.cliente)
        url = reverse('pedidos_web:crear', args=[self.producto.pk])
        self.assertContains(self.client.get(reverse('catalogo_web:productos')), url)
        self.client.post(url, {'cantidad': 1})
        self.client.post(url, {'cantidad': 1})
        otro_producto = Producto.objects.create(
            nombre='Golden', precio=Decimal('100.00'), stock=3,
            categoria=self.producto.categoria, marca=self.producto.marca,
        )
        self.client.post(reverse('pedidos_web:crear', args=[otro_producto.pk]), {'cantidad': 1})
        carrito = self.client.get(reverse('pedidos_web:carrito'))
        self.assertEqual(carrito.context['total'], Decimal('351.00'))
        self.assertFalse(Pedido.objects.filter(usuario=self.cliente).exists())
        respuesta = self.client.post(reverse('pedidos_web:confirmar_carrito'), follow=True)
        pedido = Pedido.objects.get(usuario=self.cliente)
        self.assertContains(respuesta, f'Pedido #{pedido.pk} registrado.')
        self.assertContains(respuesta, 'IPA × 2')
        self.assertNotContains(respuesta, f'Pedido #{otro_pedido.pk}</h2>')
        self.assertEqual(pedido.detalles.count(), 2)
        detalle = pedido.detalles.get(producto=self.producto)
        self.assertEqual(detalle.subtotal, self.producto.precio * 2)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 1)
        self.assertContains(self.client.get(reverse('pedidos_web:carrito')), 'Tu carrito está vacío.')

    def test_carrito_permite_editar_y_quitar_si_baja_el_stock(self):
        self.client.force_login(self.cliente)
        self.client.post(reverse('pedidos_web:crear', args=[self.producto.pk]), {'cantidad': 2})
        editar = reverse('pedidos_web:editar_carrito', args=[self.producto.pk])
        self.client.post(editar, {'accion': 'actualizar', 'cantidad': 3})
        Producto.objects.filter(pk=self.producto.pk).update(stock=1)
        respuesta = self.client.post(reverse('pedidos_web:confirmar_carrito'), follow=True)
        self.assertContains(respuesta, 'Stock insuficiente')
        self.assertEqual(respuesta.context['renglones'][0]['cantidad'], 3)
        self.assertFalse(Pedido.objects.exists())
        respuesta = self.client.post(editar, {'accion': 'quitar'}, follow=True)
        self.assertContains(respuesta, 'Tu carrito está vacío.')

    def test_pedido_sin_stock_no_guarda_encabezado_ni_detalles(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse('pedidos_web:crear', args=[self.producto.pk]), {'cantidad': 4},
        )
        self.assertContains(respuesta, 'Stock insuficiente')
        self.assertFalse(Pedido.objects.exists())

    def test_api_requiere_items_y_toma_precio_del_catalogo(self):
        cliente = APIClient()
        cliente.force_login(self.cliente)
        url = reverse('pedidos_api:pedido-list')
        self.assertEqual(cliente.post(url, {}, format='json').status_code, 400)
        respuesta = cliente.post(url, {
            'items': [{'producto': self.producto.pk, 'cantidad': 2, 'precio_unitario': '1'}],
        }, format='json')
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        pedido = Pedido.objects.get(usuario=self.cliente)
        self.assertEqual(pedido.detalles.get().precio_unitario, self.producto.precio)

    def test_compra_agota_stock_y_cancelacion_lo_devuelve_una_sola_vez(self):
        api = APIClient()
        api.force_login(self.cliente)
        lista = reverse('pedidos_api:pedido-list')
        datos = {'items': [{'producto': self.producto.pk, 'cantidad': 3}]}
        compra = api.post(lista, datos, format='json')
        self.assertEqual(compra.status_code, 201)
        self.assertEqual(api.post(lista, datos, format='json').status_code, 400)

        cancelar = reverse('pedidos_api:pedido-cancelar', args=[compra.data['id']])
        self.assertEqual(api.post(cancelar).status_code, 200)
        self.assertEqual(api.post(cancelar).status_code, 400)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_compra_fallida_revierte_descuentos_y_cancelar_un_pedido_anterior_no_repone(self):
        api = APIClient()
        api.force_login(self.cliente)
        agotado = Producto.objects.create(
            nombre='Agotado', precio=Decimal('100'), stock=0,
            categoria=self.producto.categoria, marca=self.producto.marca,
        )
        lista = reverse('pedidos_api:pedido-list')
        respuesta = api.post(lista, {'items': [
            {'producto': self.producto.pk, 'cantidad': 1},
            {'producto': agotado.pk, 'cantidad': 1},
        ]}, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Pedido.objects.exists())

        anterior = Pedido.objects.create(usuario=self.cliente)
        anterior.detalles.create(producto=self.producto, cantidad=2, precio_unitario=Decimal('100'))
        cancelar = reverse('pedidos_api:pedido-cancelar', args=[anterior.pk])
        self.assertEqual(api.post(cancelar).status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)

    def test_admin_cancela_o_elimina_pedidos_y_repone_sus_reservas(self):
        api = APIClient()
        api.force_login(self.cliente)
        admin = get_user_model().objects.create_superuser(username='admin-stock')
        self.client.force_login(admin)

        for operacion in ('cancelar', 'eliminar'):
            with self.subTest(operacion=operacion):
                compra = api.post(reverse('pedidos_api:pedido-list'), {'items': [
                    {'producto': self.producto.pk, 'cantidad': 2},
                ]}, format='json')
                self.assertEqual(compra.status_code, 201)
                pedido_id = compra.data['id']
                if operacion == 'cancelar':
                    respuesta = self.client.post(reverse('admin:pedidos_pedido_change', args=[pedido_id]), {
                        'usuario': self.cliente.pk, 'estado': 'cancelado',
                        'detalles-TOTAL_FORMS': 0, 'detalles-INITIAL_FORMS': 0,
                    })
                    self.assertEqual(Pedido.objects.get(pk=pedido_id).estado, 'cancelado')
                else:
                    respuesta = self.client.post(reverse('admin:pedidos_pedido_delete', args=[pedido_id]), {
                        'post': 'yes',
                    })
                    self.assertFalse(Pedido.objects.filter(pk=pedido_id).exists())
                self.assertEqual(respuesta.status_code, 302)
                self.producto.refresh_from_db()
                self.assertEqual(self.producto.stock, 3)

    def test_admin_crea_proveedor_y_lo_asigna_al_producto(self):
        admin = get_user_model().objects.create_superuser(username='admin')
        self.client.force_login(admin)
        url_producto = reverse('admin:catalogo_producto_change', args=[self.producto.pk])
        self.assertContains(self.client.get(url_producto), 'creá un proveedor')
        respuesta = self.client.post(reverse('admin:catalogo_proveedor_add'), {
            'nombre': 'Proveedor de prueba', 'activo': 'on', '_save': 'Guardar',
        })
        self.assertEqual(respuesta.status_code, 302)
        proveedor = Proveedor.objects.get(nombre='Proveedor de prueba')
        respuesta = self.client.post(url_producto, {
            'nombre': self.producto.nombre, 'precio': '125.50', 'stock': 3,
            'categoria': self.producto.categoria_id, 'marca': self.producto.marca_id,
            'proveedores': [proveedor.pk], '_save': 'Guardar',
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(self.producto.proveedores.filter(pk=proveedor.pk).exists())
