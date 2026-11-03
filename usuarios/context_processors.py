from django.conf import settings


def contexto_tienda(request):
    return {
        'nombre_tienda': settings.NOMBRE_TIENDA,
        'puede_gestionar_catalogo': request.user.has_perm('catalogo.add_producto')
        or request.user.has_perm('catalogo.change_producto'),
    }
