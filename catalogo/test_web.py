from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from pedidos.models import DetallePedido, Pedido
from usuarios.roles import GRUPO_GESTORES
from .models import Categoria, Marca, Producto


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CatalogoWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('configurar_grupos', stdout=StringIO())
        cls.cliente = get_user_model().objects.create_user(username='cliente')
        cls.gestor = get_user_model().objects.create_user(username='gestor')
        cls.gestor.groups.add(Group.objects.get(name=GRUPO_GESTORES))
        cls.categoria = Categoria.objects.create(nombre='Cervezas')
        cls.marca = Marca.objects.create(nombre='Artesanal')
        cls.producto = Producto.objects.create(
            nombre='IPA', precio='2500.00', stock=10,
            categoria=cls.categoria, marca=cls.marca,
        )

    def datos_producto(self, **extra):
        return dict(nombre='Porter', descripcion='Cerveza tostada', precio='3000.00', stock=4,
                    categoria=self.categoria.pk, marca=self.marca.pk, **extra)

    def test_catalogo_es_publico_y_cliente_no_ve_botones_de_edicion(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse('catalogo_web:productos'))
        self.assertContains(respuesta, 'IPA')
        self.assertNotContains(respuesta, reverse('catalogo_web:producto_editar', args=[self.producto.pk]))
        self.assertFalse(respuesta.context['puede_gestionar_catalogo'])

    def test_anonimo_redirigido_al_login_para_modificar(self):
        respuesta = self.client.get(reverse('catalogo_web:producto_crear'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta.url.startswith(reverse('usuarios:login')))

    def test_cliente_no_puede_crear_editar_ni_eliminar_por_url_directa(self):
        self.client.force_login(self.cliente)
        for nombre, args in (
            ('producto_crear', []), ('producto_editar', [self.producto.pk]),
            ('producto_eliminar', [self.producto.pk]), ('categoria_crear', []),
            ('categoria_editar', [self.categoria.pk]), ('categoria_eliminar', [self.categoria.pk]),
        ):
            with self.subTest(vista=nombre):
                url = reverse(f'catalogo_web:{nombre}', args=args)
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(Producto.objects.count(), 1)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_permiso_de_lectura_no_da_permiso_de_creacion(self):
        self.cliente.user_permissions.add(Permission.objects.get(codename='view_categoria'))
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('catalogo_web:categorias')).status_code, 200)
        self.assertEqual(self.client.post(reverse('catalogo_web:categoria_crear'), {
            'nombre': 'No autorizada',
        }).status_code, 403)

    def test_gestor_crea_edita_y_elimina_producto(self):
        self.client.force_login(self.gestor)
        self.assertRedirects(self.client.post(reverse('catalogo_web:producto_crear'),
                                              self.datos_producto()), reverse('catalogo_web:productos'))
        nuevo = Producto.objects.get(nombre='Porter')
        datos = self.datos_producto()
        datos['precio'] = '3500.00'
        self.assertRedirects(self.client.post(reverse('catalogo_web:producto_editar', args=[nuevo.pk]),
                                              datos), reverse('catalogo_web:productos'))
        nuevo.refresh_from_db()
        self.assertEqual(str(nuevo.precio), '3500.00')
        url = reverse('catalogo_web:producto_eliminar', args=[nuevo.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Producto.objects.filter(pk=nuevo.pk).exists())
        self.assertRedirects(self.client.post(url), reverse('catalogo_web:productos'))
        self.assertFalse(Producto.objects.filter(pk=nuevo.pk).exists())

    def test_gestor_crea_edita_y_elimina_categoria(self):
        self.client.force_login(self.gestor)
        self.assertRedirects(self.client.post(reverse('catalogo_web:categoria_crear'), {
            'nombre': 'Sidras',
        }), reverse('catalogo_web:categorias'))
        categoria = Categoria.objects.get(nombre='Sidras')
        self.client.post(reverse('catalogo_web:categoria_editar', args=[categoria.pk]), {
            'nombre': 'Sidras artesanales',
        })
        categoria.refresh_from_db()
        self.assertEqual(categoria.nombre, 'Sidras artesanales')
        self.assertRedirects(self.client.post(reverse('catalogo_web:categoria_eliminar', args=[categoria.pk])),
                             reverse('catalogo_web:categorias'))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_categoria_con_productos_no_se_elimina_ni_falla_con_500(self):
        self.client.force_login(self.gestor)
        respuesta = self.client.post(reverse('catalogo_web:categoria_eliminar', args=[self.categoria.pk]))
        self.assertContains(respuesta, 'No se puede eliminar')
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_producto_en_pedido_no_se_elimina_ni_falla_con_500(self):
        pedido = Pedido.objects.create(usuario=self.cliente)
        DetallePedido.objects.create(pedido=pedido, producto=self.producto, cantidad=1, precio_unitario='2500.00')
        self.client.force_login(self.gestor)
        respuesta = self.client.post(reverse('catalogo_web:producto_eliminar', args=[self.producto.pk]))
        self.assertContains(respuesta, 'No se puede eliminar')
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())

    def test_precio_negativo_y_archivo_falso_se_rechazan(self):
        self.client.force_login(self.gestor)
        datos = self.datos_producto(imagen=SimpleUploadedFile('falsa.jpg', b'no es una imagen'))
        datos['precio'] = '-1.00'
        respuesta = self.client.post(reverse('catalogo_web:producto_crear'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('precio', respuesta.context['form'].errors)
        self.assertIn('imagen', respuesta.context['form'].errors)
        self.assertFalse(Producto.objects.filter(nombre='Porter').exists())

    def test_gestor_puede_cargar_imagen_valida(self):
        self.client.force_login(self.gestor)
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            buffer = BytesIO()
            Image.new('RGB', (4, 4), 'green').save(buffer, format='PNG')
            imagen = SimpleUploadedFile('producto.png', buffer.getvalue(), content_type='image/png')
            respuesta = self.client.post(reverse('catalogo_web:producto_crear'), self.datos_producto(imagen=imagen))
            self.assertEqual(respuesta.status_code, 302)
            self.assertTrue(Path(Producto.objects.get(nombre='Porter').imagen.path).exists())

    def test_busqueda_paginada_conserva_busqueda_en_los_enlaces(self):
        Producto.objects.bulk_create([
            Producto(nombre=f'IPA {i:02}', precio='1000.00', stock=2,
                     categoria=self.categoria, marca=self.marca) for i in range(13)
        ])
        url = reverse('catalogo_web:productos')
        primera = self.client.get(url, {'q': 'IPA'})
        self.assertEqual(len(primera.context['productos']), 12)
        self.assertContains(primera, 'q=IPA&amp;page=2')
        self.assertNotContains(primera, '??')
        segunda = self.client.get(url, {'q': 'IPA', 'page': 2})
        self.assertEqual(len(segunda.context['productos']), 2)

    def test_nombre_de_producto_se_muestra_escapado(self):
        self.producto.nombre = '<script>alert(1)</script>'
        self.producto.save()
        respuesta = self.client.get(reverse('catalogo_web:productos'))
        self.assertContains(respuesta, '&lt;script&gt;')
        self.assertNotContains(respuesta, '<script>alert(1)</script>')
