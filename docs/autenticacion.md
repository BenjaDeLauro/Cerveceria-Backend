# Autenticación, permisos y templates de Django

## Qué incorpora esta parte

Registro, login y logout con sesiones; autenticación por token para la API; grupos y permisos de Django; una bienvenida con template; administración de productos y categorías con Django Admin.

Se utilizan las vistas y formularios de autenticación de Django, el usuario personalizado existente y `rest_framework.authtoken`. No se agregan modelos de usuario paralelos ni dependencias nuevas al gestor uv.

## Preparación

```shell
uv sync --locked
uv run python manage.py migrate
uv run python manage.py configurar_grupos
uv run python manage.py runserver
```

La migración habilita las tablas de authtoken provistas por DRF. No modifica ni borra los diez modelos de la cervecería. Si no existe un administrador, se crea con `uv run python manage.py createsuperuser`.

## Rutas de las pantallas

| Ruta | Función | Acceso |
| --- | --- | --- |
| `/` | Bienvenida del backend | Público |
| `/usuarios/registro/` | Registro con validación de contraseña | Visitantes |
| `/usuarios/login/` | Inicio de sesión | Visitantes |
| `/usuarios/logout/` | Cierre de sesión, solo POST con CSRF | Usuario conectado |
| `/admin/` | Administración de todos los modelos | Personal con los permisos correspondientes |


## Grupos

| Perfil | Consulta pública | Gestión del catálogo | Usuarios y permisos |
| --- | --- | --- | --- |
| Visitante | Sí | No | No |
| Clientes | Sí | No | No |
| Gestores de catálogo | Sí | Según sus permisos de catálogo | No |
| Superusuario | Sí | Sí | Sí |

`configurar_grupos` crea Clientes y Gestores de catálogo. Asigna al segundo los permisos de los modelos de `catalogo`; puede repetirse y conserva permisos adicionales ya asignados. La creación pública de cuentas solo asigna Clientes y no acepta `is_staff`, `is_superuser`, grupos ni permisos enviados desde el formulario.

Para dar acceso de gestión, un administrador abre Usuarios en `/admin/`, selecciona la cuenta y agrega el grupo Gestores de catálogo. Para permitir además la entrada a Django Admin se debe marcar «Es staff» explícitamente.

## Contrato de autenticación para la API

### Obtener un token

`POST /api/auth/login/`, sin un encabezado Authorization anterior:

```json
{"username": "tu_usuario", "password": "tu_contraseña"}
```

Respuesta 200:

```json
{"token": "valor_del_token", "usuario": {"id": 1, "username": "tu_usuario"}}
```

Credenciales incorrectas o usuario inactivo devuelven 400. El endpoint limita los intentos a 10 por minuto mediante el throttling de DRF. El token se reutiliza hasta revocarlo. La contraseña no se devuelve ni se almacena en texto plano.

### Consultar la cuenta

`GET /api/auth/me/` con:

```text
Authorization: Token valor_del_token
```

Devuelve únicamente los datos de la cuenta autenticada: id, username, nombre, apellido y email. También admite una sesión de Django válida. El orden de autenticadores es SessionAuthentication y luego TokenAuthentication; las peticiones no autenticadas se rechazan con 403.

### Revocar el token

`POST /api/auth/logout/` con el mismo encabezado revoca el token y responde 204. Las solicitudes posteriores con ese token se rechazan. Si se usa una sesión, también se cierra esa sesión y se exige CSRF para el POST. El logout de la pantalla web cierra su sesión; la revocación de tokens se realiza mediante este endpoint de API.

### Integración con la rama de catálogo

- La configuración global permite SessionAuthentication y TokenAuthentication. Las vistas de catálogo conservan sus propias reglas de permisos.
- Las escrituras del catálogo requieren personal autenticado con los permisos de la API.
- `/api/auth/` y `/api-auth/` no ocupan las rutas `/api/productos/`, `/api/categorias/` ni `/api/marcas/`.
- `/api-auth/login/` habilita el acceso por sesión de la API navegable de DRF.
- Los futuros endpoints que operen con pedidos o direcciones deben validar la pertenencia al usuario, como establece la planificación de modelos.

## Archivos principales

- `usuarios/forms.py`, `views.py` y `urls.py`: registro, login y logout de las pantallas.
- `usuarios/api.py` y `urls_api.py`: autenticación por tokens, consulta de cuenta y revocación.
- `usuarios/context_processors.py`: nombre de la tienda.
- `usuarios/management/commands/configurar_grupos.py`: preparación reproducible de roles.
- `templates/` y `static/css/tienda.css`: interfaz de Django.
- `usuarios/test_autenticacion.py`: pruebas de los flujos y límites de acceso.

## Verificación

Ejecutar "uv run python manage.py test" para comprobar autenticación, permisos y API.
