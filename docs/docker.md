# Backend con Docker — EFI de Ingeniería de Software

Este aporte permite ejecutar el backend local de la EFI sin instalar Python ni uv
en el equipo anfitrión. La imagen usa Python 3.14 y uv 0.13.6; instala las
dependencias exactas de `uv.lock` con `uv sync --locked`. No agrega modelos ni
cambia el contrato de la API de Ignacio.

## Requisitos y primer inicio

Se necesita Docker Engine o Docker Desktop iniciado, con contenedores Linux y
Docker Compose v2. Desde la raíz del repositorio:

```powershell
Copy-Item .env.example .env
docker compose up --build -d --wait
docker compose exec web python manage.py createsuperuser
```

En Linux/macOS, el primer comando es `cp .env.example .env`. Copiar el ejemplo
solamente la primera vez, para conservar la configuración propia. El archivo
`.env` queda fuera de Git y de la imagen.

Al iniciar el servidor se aplican las migraciones y se configura el comando
idempotente de grupos. No se crean administradores ni contraseñas automáticamente.

- Bienvenida: <http://127.0.0.1:8000/>.
- Catálogo: <http://127.0.0.1:8000/catalogo/productos/>.
- Administración: <http://127.0.0.1:8000/admin/>.
- API de productos: <http://127.0.0.1:8000/api/productos/>.

Para agregar los tres productos de demostración, sin sobrescribir los existentes:

```shell
docker compose exec web python manage.py cargar_catalogo_demo
```

Dentro de esta imagen no se incluye el repositorio del frontend. El comando demo
crea los productos con precio/stock de prueba y las tarjetas muestran la imagen
por defecto hasta que un administrador cargue las fotografías.

## Configuración

| Variable | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave de Django; reemplazar el ejemplo por una clave propia. |
| `DJANGO_DEBUG` | `true` para la demostración local, incluidos estáticos y archivos multimedia. |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceptados, separados por comas, sin protocolo ni puerto. |
| `CORS_ALLOWED_ORIGINS` | Orígenes completos del frontend, separados por comas. |
| `BACKEND_PORT` | Puerto del equipo anfitrión; por defecto `8000`. |

Si el puerto 8000 está ocupado, cambiar `BACKEND_PORT=8001` en `.env` y volver a
ejecutar `docker compose up -d`. En el frontend, ajustar
`NEXT_PUBLIC_API_URL=http://127.0.0.1:8001/api/` y reiniciar Next.js.

Compose publica el puerto solamente en `127.0.0.1`. La imagen usa un usuario sin
privilegios y el servidor de desarrollo de Django con `--noreload`: está pensada
para la demostración local de la EFI, no como despliegue público de producción.

## Persistencia

Compose crea dos volúmenes con el nombre del proyecto como prefijo:

- `database`, montado en `/app/data`: conserva SQLite, usuarios y tokens.
- `media`, montado en `/app/media`: conserva las imágenes cargadas.

`docker compose down` detiene y elimina los contenedores, pero conserva estos
volúmenes. Al reconstruir o recrear el servicio se reutilizan los mismos datos.
No usar `down --volumes` si se quieren conservar. La base `db.sqlite3` utilizada
fuera de Docker no se copia ni se migra automáticamente al volumen del contenedor.

En ejecución nativa, sin esas variables, Django sigue usando `db.sqlite3` y
`media/` en la raíz del proyecto. `DJANGO_DATA_DIR` y `DJANGO_MEDIA_ROOT` permiten
elegir otras carpetas existentes; Compose las fija dentro del contenedor.

## Verificación y uso cotidiano

```shell
docker compose ps
docker compose logs -f web
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py test
docker compose down
```

Si cambia código, dependencias o configuración, ejecutar nuevamente
`docker compose up --build -d --wait`. No se monta el código fuente del equipo
encima de la imagen, para que se pruebe lo que realmente se construyó.

El workflow **Verificar Docker** construye la imagen en Linux, ejecuta las pruebas
de Django, consulta bienvenida/catálogo/API/admin/CSS y comprueba que la base y un
archivo multimedia sobrevivan a la recreación del contenedor. El resultado de esa
ejecución en Actions es la evidencia de validación del contenedor.

Referencias: [uv en Docker](https://docs.astral.sh/uv/guides/integration/docker/)
y [servicios de Compose](https://docs.docker.com/reference/compose-file/services/).
