from django.urls import path

from . import vistas_web as views

app_name = 'catalogo_web'
urlpatterns = [
    path('productos/', views.ProductoListView.as_view(), name='productos'),
    path('productos/nuevo/', views.ProductoCreateView.as_view(), name='producto_crear'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_eliminar'),
    path('categorias/', views.CategoriaListView.as_view(), name='categorias'),
    path('categorias/nueva/', views.CategoriaCreateView.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_eliminar'),
]
