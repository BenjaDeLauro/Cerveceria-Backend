from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework.exceptions import ValidationError

from catalogo.models import Producto
from .serializers import PedidoCompraSerializer


class CantidadPedidoForm(forms.Form):
    cantidad = forms.IntegerField(min_value=1, max_value=2147483647, initial=1)


CLAVE_CARRITO = 'carrito_pedidos'


@login_required
@require_http_methods(['GET', 'POST'])
def crear_pedido(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = CantidadPedidoForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        carrito = request.session.get(CLAVE_CARRITO, {})
        clave = str(pk)
        cantidad = carrito.get(clave, 0) + form.cleaned_data['cantidad']
        if cantidad > producto.stock:
            form.add_error('cantidad', f'Stock insuficiente. Disponibles: {producto.stock}.')
        else:
            carrito[clave] = cantidad
            request.session[CLAVE_CARRITO] = carrito
            messages.success(request, f'{producto.nombre} se agregó al carrito.')
            return redirect('pedidos_web:carrito')
    return render(request, 'pedidos/nuevo.html', {'producto': producto, 'form': form})


@login_required
def ver_carrito(request):
    carrito = request.session.get(CLAVE_CARRITO, {})
    productos = Producto.objects.in_bulk([int(pk) for pk in carrito])
    renglones = []
    total = 0
    disponible = bool(carrito)
    for clave, cantidad in carrito.items():
        producto = productos.get(int(clave))
        subtotal = producto.precio * cantidad if producto else 0
        hay_stock = producto is not None and cantidad <= producto.stock
        disponible = disponible and hay_stock
        renglones.append({
            'id': clave, 'producto': producto, 'cantidad': cantidad,
            'subtotal': subtotal, 'hay_stock': hay_stock,
        })
        total += subtotal
    return render(request, 'pedidos/carrito.html', {
        'renglones': renglones, 'total': total, 'disponible': disponible,
    })


@login_required
@require_POST
def editar_carrito(request, pk):
    carrito = request.session.get(CLAVE_CARRITO, {})
    clave = str(pk)
    if clave not in carrito:
        return redirect('pedidos_web:carrito')

    if request.POST.get('accion') == 'quitar':
        carrito.pop(clave)
    else:
        producto = Producto.objects.filter(pk=pk).first()
        form = CantidadPedidoForm(request.POST)
        if not form.is_valid() or producto is None:
            messages.error(request, 'Ingresá una cantidad válida para un producto disponible.')
            return redirect('pedidos_web:carrito')
        cantidad = form.cleaned_data['cantidad']
        if cantidad > producto.stock:
            messages.error(request, f'Stock insuficiente para {producto.nombre}. Disponibles: {producto.stock}.')
            return redirect('pedidos_web:carrito')
        carrito[clave] = cantidad

    request.session[CLAVE_CARRITO] = carrito
    return redirect('pedidos_web:carrito')


@login_required
@require_POST
def confirmar_carrito(request):
    carrito = request.session.get(CLAVE_CARRITO, {})
    if not carrito:
        messages.error(request, 'Agregá al menos un producto para hacer el pedido.')
        return redirect('pedidos_web:carrito')
    serializer = PedidoCompraSerializer(
        data={'items': [{'producto': int(pk), 'cantidad': cantidad} for pk, cantidad in carrito.items()]},
        context={'request': request},
    )
    if not serializer.is_valid():
        messages.error(request, 'Revisá los productos y las cantidades del carrito.')
        return redirect('pedidos_web:carrito')
    try:
        pedido = serializer.save(usuario=request.user)
    except ValidationError as exc:
        messages.error(request, str(exc.detail['items']))
        return redirect('pedidos_web:carrito')

    request.session.pop(CLAVE_CARRITO)
    messages.success(request, f'Pedido #{pedido.pk} registrado.')
    return redirect('pedidos_web:lista')


@login_required
def mis_pedidos(request):
    pedidos = request.user.pedidos.prefetch_related('detalles__producto').order_by('-fecha', '-pk')
    return render(request, 'pedidos/lista.html', {'pedidos': pedidos})
