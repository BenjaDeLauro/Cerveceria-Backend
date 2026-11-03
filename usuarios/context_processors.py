from django.conf import settings


def contexto_tienda(request):
    return {
        'nombre_tienda': settings.NOMBRE_TIENDA,
    }
