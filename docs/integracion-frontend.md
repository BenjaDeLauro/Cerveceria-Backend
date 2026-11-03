# Integración local con ImperioSur

La rama `feature/integracion-frontend` parte de `feature/autenticacion` y reúne la API existente de `feature/api-rest`. Los cambios quedan en una rama de integración para revisión del equipo.

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
uv run python manage.py runserver
```

Frontend, desde la carpeta vecina `ImperioSur-Frontend`:

```powershell
# Sólo si faltan las dependencias: npm ci
Copy-Item .env.example .env.local
npm run dev
```

Abrir http://127.0.0.1:3000/cervezas. En el frontend, `NEXT_PUBLIC_API_URL` debe apuntar a `http://127.0.0.1:8000/api/`.

## Verificación manual

Cargar un producto desde Django Admin y abrir su ficha en el frontend.

## Validación y tareas

Ejecutar las pruebas de Django para comprobar modelos, administración, autenticación y API. La integración cubre búsqueda, filtro por categoría, paginación, CORS y revocación de tokens.

Se respetan las responsabilidades acordadas: Benjamín, estructura e integración general; Esteban, autenticación/templates/modelos; Ignacio, API REST. Esta rama adapta el contrato para la conexión del frontend, sin completar por anticipado los demás ViewSets asignados a API. Aún faltan requisitos generales de la consigna (ocho ViewSets, segundo anidado, actions, documentación OpenAPI y Docker) y flujos del frontend; la conexión de lectura no implica que la EFI esté completa.
