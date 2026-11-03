from django.urls import path

from .views import IngresoView, RegistroView, SalidaView

app_name = 'usuarios'
urlpatterns = [
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', IngresoView.as_view(), name='login'),
    path('logout/', SalidaView.as_view(), name='logout'),
]
