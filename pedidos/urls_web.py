from django.urls import path

from . import vistas_web

app_name = 'pedidos_web'
urlpatterns = [
    path('', vistas_web.mis_pedidos, name='lista'),
    path('nuevo/<int:pk>/', vistas_web.crear_pedido, name='crear'),
    path('carrito/', vistas_web.ver_carrito, name='carrito'),
    path('carrito/<int:pk>/', vistas_web.editar_carrito, name='editar_carrito'),
    path('carrito/confirmar/', vistas_web.confirmar_carrito, name='confirmar_carrito'),
]
