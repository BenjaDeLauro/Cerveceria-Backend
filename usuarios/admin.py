from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active'
    )

    list_filter = ('is_staff', 'is_active', 'groups')

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )

    ordering = ('username',)