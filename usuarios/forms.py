from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario


class RegistroForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {'first_name': 'Nombre', 'last_name': 'Apellido'}


class IngresoForm(AuthenticationForm):
    username = forms.CharField(label='Usuario', widget=forms.TextInput(
        attrs={'autofocus': True, 'autocomplete': 'username'},
    ))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(
        attrs={'autocomplete': 'current-password'},
    ))
