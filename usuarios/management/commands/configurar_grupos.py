from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from usuarios.roles import GRUPO_CLIENTES, GRUPO_GESTORES


class Command(BaseCommand):
    help = 'Crea los grupos Clientes y Gestores de catálogo y configura sus permisos.'

    @transaction.atomic
    def handle(self, *args, **options):
        Group.objects.get_or_create(name=GRUPO_CLIENTES)
        gestores, _ = Group.objects.get_or_create(name=GRUPO_GESTORES)
        permisos = Permission.objects.filter(content_type__app_label='catalogo')
        if not permisos.exists():
            self.stderr.write('Primero ejecutá python manage.py migrate.')
            return
        # add es idempotente y conserva permisos adicionales asignados por el grupo.
        gestores.permissions.add(*permisos)
        self.stdout.write(self.style.SUCCESS('Grupos y permisos de catálogo configurados.'))
