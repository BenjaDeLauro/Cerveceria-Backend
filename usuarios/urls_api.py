from django.urls import path

from .api import LoginTokenView, LogoutTokenView, UsuarioActualView

app_name = 'autenticacion_api'
urlpatterns = [
    path('login/', LoginTokenView.as_view(), name='login'),
    path('logout/', LogoutTokenView.as_view(), name='logout'),
    path('me/', UsuarioActualView.as_view(), name='me'),
]
