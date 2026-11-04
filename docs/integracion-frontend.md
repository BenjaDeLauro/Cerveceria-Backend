# Integración local con ImperioSur

El backend se ejecuta desde `main`. El código del catálogo de Next.js está en la rama [`feature/integracion-api` de ImperioSur-Frontend](https://github.com/EstebanjsrZ/ImperioSur-Frontend/tree/feature/integracion-api). Usá esa rama para las pruebas hasta que el equipo la integre a su rama principal.

## Contrato del catálogo

- `GET /api/productos/`: lista pública con categoría y marca anidadas.
- Parámetros `search`, `categoria` (ID), `page`, `page_size` (máximo 100, defecto 6).
- Respuesta de lista: `{ "count": 3, "next": null, "previous": null, "results": [...] }`. El mismo formato paginado se aplica a categorías y marcas; los consumidores anteriores de arrays deben leer `results`.
- `GET /api/productos/{id}/`: detalle con categoría y marca como IDs. Se mantiene la regla de anidado únicamente en list.
- `GET /api/categorias/`, `/api/marcas/` y sus detalles: resuelven los filtros y los nombres de las relaciones.
- Las modificaciones siguen requiriendo personal autenticado. Sesión y Token permanecen habilitados; el consumo público del catálogo no requiere token.

CORS permite `http://127.0.0.1:3000` y `http://localhost:3000`, sólo en `/api/`. Para otro origen, definir `$env:CORS_ALLOWED_ORIGINS='https://frontend.example'` antes de iniciar Django. No se habilitan todos los orígenes ni credenciales cruzadas de sesión.

Se emplean [paginación de DRF](https://www.django-rest-framework.org/api-guide/pagination/), [SearchFilter y parámetros de consulta](https://www.django-rest-framework.org/api-guide/filtering/) y [django-cors-headers](https://github.com/adamchainz/django-cors-headers).

## Ejecución en dos terminales

Backend, desde esta carpeta:

```powershell
uv sync --locked
uv run python manage.py migrate
uv run python manage.py cargar_catalogo_demo
uv run python manage.py runserver
```

Frontend, desde la carpeta vecina `ImperioSur-Frontend`:

```powershell
npm ci
if (-not (Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm run dev
```

En Linux o macOS, copiar `.env.example` a `.env.local` con `cp` la primera vez. Abrir [el catálogo del frontend](http://127.0.0.1:3000/cervezas). En el frontend, `NEXT_PUBLIC_API_URL` debe apuntar a `http://127.0.0.1:8000/api/`.

## Datos de demostración

`uv run python manage.py cargar_catalogo_demo` carga IPA, Golden, Stout, Red Ale, Honey y Porter con sus imágenes de muestra. Las imágenes originales están en `catalogo/demo_images/`. Si los productos ya existen, el comando completa las imágenes que falten y conserva sus precios, stock y fotos ya cargadas.

Para comprobar el circuito, editar un producto desde `/admin/catalogo/producto/` y volver a cargar su ficha en el frontend.

## Pedidos y stock

El carrito de Django y `POST /api/pedidos/` usan la misma regla. Al crear el pedido se descuentan las unidades disponibles. Si falla un renglón, se deshace toda la operación. El precio unitario se toma del catálogo.

Cancelar un pedido con stock descontado devuelve sus unidades una sola vez. Eliminar un pedido pendiente también libera las unidades. Los pedidos anteriores a este cambio y los cargados manualmente en el admin no descontaron stock, por lo que no generan una devolución. En el admin se pueden gestionar los estados de los pedidos de clientes y consultar sus renglones; esos renglones conservan la reserva original.

## Verificación

- Backend: `uv run python manage.py test`.
- Frontend: `npm test` y `npm run build`.
- En el navegador, buscar una cerveza y abrir su ficha para comprobar que se muestran los datos y la imagen servidos por Django. El carrito y el historial se prueban en el sitio Django; la rama de Next.js indicada arriba consume el catálogo.
