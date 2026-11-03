# ImperioSur — Backend de Ingeniería de Software

Sistema de gestión de catálogo, clientes y pedidos de una cervecería y tienda de bebidas artesanales. Backend de la EFI 2026 de Ingeniería de Software, conectado al frontend ImperioSur de Programación III mediante la API de catálogo.

## Integración con el frontend

El frontend de Programación III consume la API de este backend. El contrato y los datos de prueba se detallan en [docs/integracion-frontend.md](docs/integracion-frontend.md).

## Integrantes

- Benjamín De Lauro
- Ignacio Piñeiro
- Esteban Rodríguez

## Tecnologías

Python, Django, Django REST Framework, SQLite y uv. Las dependencias se fijan en `uv.lock`.

## Planificación de la base de datos

La consigna vigente requiere al menos **10 modelos propios relacionados**. A los seis modelos iniciales se suman Presentacion, Proveedor, DireccionEnvio y Resena. La planificación de campos, relaciones y reglas se encuentra en [docs/modelos.md](docs/modelos.md).

```mermaid
erDiagram
    Usuario ||--o{ Pedido : realiza
    Usuario ||--o{ DireccionEnvio : registra
    DireccionEnvio o|--o{ Pedido : recibe
    Pedido ||--o{ DetallePedido : contiene
    Producto ||--o{ DetallePedido : integra
    Categoria ||--o{ Producto : clasifica
    Marca ||--o{ Producto : identifica
    Presentacion o|--o{ Producto : describe
    Proveedor }o--o{ Producto : abastece
    Usuario ||--o{ Resena : escribe
    Producto ||--o{ Resena : recibe
```

## Ejecución local

Se necesita Python 3.12 o superior y [uv](https://docs.astral.sh/uv/).

```shell
uv sync --locked
uv run python manage.py migrate
uv run python manage.py configurar_grupos
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

La bienvenida está disponible en `http://127.0.0.1:8000/` y el administrador en `http://127.0.0.1:8000/admin/`. La base SQLite, los usuarios locales, las imágenes y `.venv` no se suben a Git.

## Ejecución con Docker

Con Docker iniciado y Compose v2, desde la raíz del repositorio:

```powershell
Copy-Item .env.example .env
docker compose up --build -d --wait
docker compose exec web python manage.py createsuperuser
```

En Linux/macOS usar `cp .env.example .env` en el primer paso. El ejemplo se copia
solo la primera vez. Las migraciones y los grupos se preparan al iniciar el
servidor. SQLite y las imágenes se conservan en volúmenes separados. La aplicación
queda disponible en `http://127.0.0.1:8000/`.

Los comandos de pruebas, variables, persistencia y conexión con el frontend se
explican en [docs/docker.md](docs/docker.md). El workflow **Verificar Docker**
construye y prueba el contenedor en GitHub Actions.

## Usuarios, pantallas y permisos

- Registro: `/usuarios/registro/`. Crea una cuenta del grupo **Clientes** y abre su sesión.
- Login: `/usuarios/login/`. Logout mediante POST: `/usuarios/logout/`.
- Gestión de productos y categorías desde Django Admin.
- Grupo **Gestores de catálogo** configurado mediante `configurar_grupos`. Un administrador puede asignarlo desde Usuarios. El comando se puede repetir y no convierte a sus miembros en personal ni superusuarios.
- Context processor propio, mensajes de confirmación, CSRF y pantallas adaptables a dispositivos móviles.
- API de autenticación por token: `/api/auth/login/`, `/api/auth/me/` y `/api/auth/logout/`. También se habilitan las sesiones y el acceso navegable en `/api-auth/login/`.

Los pasos de prueba, la matriz de permisos y el contrato para integrar la API se detallan en [docs/autenticacion.md](docs/autenticacion.md).

## Captura de funcionamiento

![Documentación Swagger de la API](docs/capturas/swagger.jpg)

## Verificación

```shell
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

## Entrega y trabajo en curso

Esta versión reúne los aportes de modelos, administración, autenticación, API REST y Docker. La API navegable está disponible en `/api/productos/`, Swagger en `/api/docs/` y el esquema OpenAPI en `/api/schema/`.

La API registra ocho ViewSets: productos, categorías, marcas, presentaciones, proveedores, direcciones, pedidos y detalles de pedido. Los listados de productos y pedidos incluyen relaciones anidadas. Las acciones de pedidos permiten consultar el total y cancelar un pedido pendiente.

Seguimos trabajando en los detalles de la consigna y en la verificación con el frontend. Los cambios posteriores se preparan en ramas de trabajo y se revisan antes de integrarlos a `main`.
