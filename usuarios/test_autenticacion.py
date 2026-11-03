from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from .roles import GRUPO_CLIENTES, GRUPO_GESTORES

CLAVE = 'UnaClaveSegura!2026'
HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@override_settings(PASSWORD_HASHERS=HASHERS)
class AutenticacionWebTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username='cliente', password=CLAVE)

    def test_bienvenida_login_y_registro_son_publicos(self):
        for nombre in ('inicio', 'usuarios:login', 'usuarios:registro'):
            with self.subTest(nombre=nombre):
                respuesta = self.client.get(reverse(nombre))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.context['nombre_tienda'], 'Cervecería y Bebidas Artesanales')
        self.assertContains(self.client.get(reverse('usuarios:login')), 'csrfmiddlewaretoken')

    def test_registro_crea_cliente_sin_elevar_privilegios_y_abre_sesion(self):
        respuesta = self.client.post(reverse('usuarios:registro'), {
            'username': 'cliente_nuevo', 'email': 'cliente@example.com',
            'password1': CLAVE, 'password2': CLAVE,
            'is_staff': True, 'is_superuser': True, 'groups': [999],
        })
        self.assertRedirects(respuesta, reverse('inicio'))
        usuario = get_user_model().objects.get(username='cliente_nuevo')
        self.assertTrue(usuario.check_password(CLAVE))
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(list(usuario.groups.values_list('name', flat=True)), [GRUPO_CLIENTES])
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_registro_rechaza_clave_debil_y_claves_distintas(self):
        for primera, segunda in [('123', '123'), (CLAVE, 'Diferente!')]:
            with self.subTest(primera=primera):
                respuesta = self.client.post(reverse('usuarios:registro'), {
                    'username': 'invalido', 'email': 'invalido@example.com',
                    'password1': primera, 'password2': segunda,
                })
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context['form'].errors)
                self.assertFalse(get_user_model().objects.filter(username='invalido').exists())

    def test_registro_rechaza_usuario_repetido(self):
        respuesta = self.client.post(reverse('usuarios:registro'), {
            'username': 'cliente', 'email': 'otro@example.com',
            'password1': CLAVE, 'password2': CLAVE,
        })
        self.assertIn('username', respuesta.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_usuario_autenticado_no_repite_registro(self):
        self.client.force_login(self.usuario)
        self.assertRedirects(self.client.get(reverse('usuarios:registro')), reverse('inicio'))

    def test_login_valido_respeta_destino_interno(self):
        respuesta = self.client.post(reverse('usuarios:login'), {
            'username': 'cliente', 'password': CLAVE, 'next': reverse('catalogo_web:productos'),
        })
        self.assertRedirects(respuesta, reverse('catalogo_web:productos'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.usuario.pk)

    def test_login_no_redirige_a_dominio_externo(self):
        respuesta = self.client.post(reverse('usuarios:login'), {
            'username': 'cliente', 'password': CLAVE, 'next': 'https://externo.example/',
        })
        self.assertRedirects(respuesta, reverse('inicio'))

    def test_login_rechaza_clave_incorrecta_y_usuario_inactivo(self):
        for activa, clave in [(True, 'incorrecta'), (False, CLAVE)]:
            self.usuario.is_active = activa
            self.usuario.save()
            respuesta = self.client.post(reverse('usuarios:login'), {
                'username': 'cliente', 'password': clave,
            })
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_solo_por_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('usuarios:logout')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post(reverse('usuarios:logout')), reverse('inicio'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_y_logout_exigen_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        url = reverse('usuarios:login')
        self.assertEqual(cliente.post(url, {'username': 'cliente', 'password': CLAVE}).status_code, 403)
        cliente.get(url)
        respuesta = cliente.post(url, {'username': 'cliente', 'password': CLAVE,
                                      'csrfmiddlewaretoken': cliente.cookies['csrftoken'].value})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(cliente.post(reverse('usuarios:logout')).status_code, 403)
        self.assertEqual(cliente.post(reverse('usuarios:logout'), {
            'csrfmiddlewaretoken': cliente.cookies['csrftoken'].value,
        }).status_code, 302)

    def test_registro_exige_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        self.assertEqual(cliente.post(reverse('usuarios:registro'), {}).status_code, 403)

    def test_configuracion_de_grupos_es_idempotente_y_no_da_permisos_a_clientes(self):
        call_command('configurar_grupos', stdout=StringIO())
        call_command('configurar_grupos', stdout=StringIO())
        self.assertEqual(Group.objects.filter(name=GRUPO_CLIENTES).count(), 1)
        self.assertEqual(Group.objects.filter(name=GRUPO_GESTORES).count(), 1)
        self.assertFalse(Group.objects.get(name=GRUPO_CLIENTES).permissions.exists())
        self.usuario.groups.add(Group.objects.get(name=GRUPO_GESTORES))
        usuario = get_user_model().objects.get(pk=self.usuario.pk)
        self.assertTrue(usuario.has_perm('catalogo.add_producto'))
        self.assertTrue(usuario.has_perm('catalogo.delete_categoria'))
        self.assertFalse(usuario.has_perm('usuarios.change_usuario'))
        self.assertFalse(usuario.is_staff)


@override_settings(PASSWORD_HASHERS=HASHERS)
class AutenticacionTokenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='cliente_api', email='api@example.com', password=CLAVE,
        )

    def setUp(self):
        cache.clear()
        self.api = APIClient()

    def ingresar(self):
        respuesta = self.api.post(reverse('autenticacion_api:login'), {
            'username': 'cliente_api', 'password': CLAVE,
        }, format='json')
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.data['token']

    def test_login_emite_token_y_me_devuelve_solo_el_usuario_autenticado(self):
        token = self.ingresar()
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        respuesta = self.api.get(reverse('autenticacion_api:me'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['id'], self.usuario.pk)
        self.assertEqual(respuesta.data['email'], 'api@example.com')
        self.assertNotIn('password', respuesta.data)
        self.assertEqual(Token.objects.get(user=self.usuario).key, token)

    def test_login_repetido_reutiliza_token_hasta_revocarlo(self):
        self.assertEqual(self.ingresar(), self.ingresar())
        self.assertEqual(Token.objects.count(), 1)

    def test_me_requiere_autenticacion(self):
        self.assertEqual(self.api.get(reverse('autenticacion_api:me')).status_code, 403)

    def test_login_invalido_no_emite_token(self):
        respuesta = self.api.post(reverse('autenticacion_api:login'), {
            'username': 'cliente_api', 'password': 'incorrecta',
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Token.objects.exists())

    def test_usuario_inactivo_no_obtiene_token(self):
        self.usuario.is_active = False
        self.usuario.save()
        respuesta = self.api.post(reverse('autenticacion_api:login'), {
            'username': 'cliente_api', 'password': CLAVE,
        }, format='json')
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Token.objects.exists())

    def test_logout_revoca_token_y_no_admite_get(self):
        token = self.ingresar()
        self.api.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.api.get(reverse('autenticacion_api:logout')).status_code, 405)
        self.assertEqual(self.api.post(reverse('autenticacion_api:logout')).status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.usuario).exists())
        self.assertEqual(self.api.get(reverse('autenticacion_api:me')).status_code, 403)

    def test_sesion_tambien_autentica_api_y_logout_exige_csrf(self):
        cliente = APIClient(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.get(reverse('autenticacion_api:me')).status_code, 200)
        self.assertEqual(cliente.post(reverse('autenticacion_api:logout')).status_code, 403)

    def test_intentos_de_login_excesivos_se_limitan(self):
        with patch.object(ScopedRateThrottle, 'THROTTLE_RATES', {'autenticacion': '2/min'}):
            for _ in range(2):
                respuesta = self.api.post(reverse('autenticacion_api:login'), {
                    'username': 'cliente_api', 'password': 'incorrecta',
                }, format='json')
                self.assertEqual(respuesta.status_code, 400)
            self.assertEqual(self.api.post(reverse('autenticacion_api:login'), {
                'username': 'cliente_api', 'password': 'incorrecta',
            }, format='json').status_code, 429)
