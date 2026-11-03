from django.contrib.auth import logout
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView


class LoginTokenView(ObtainAuthToken):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'autenticacion'

    @extend_schema(responses=inline_serializer(
        name='LoginTokenResponse',
        fields={
            'token': serializers.CharField(),
            'usuario': inline_serializer(
                name='UsuarioToken', fields={
                    'id': serializers.IntegerField(),
                    'username': serializers.CharField(),
                },
            ),
        },
    ))
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=usuario)
        return Response({'token': token.key, 'usuario': {
            'id': usuario.pk, 'username': usuario.username,
        }})


class UsuarioActualView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=inline_serializer(
        name='UsuarioActualResponse',
        fields={
            'id': serializers.IntegerField(),
            'username': serializers.CharField(),
            'nombre': serializers.CharField(),
            'apellido': serializers.CharField(),
            'email': serializers.EmailField(),
        },
    ))
    def get(self, request):
        return Response({
            'id': request.user.pk, 'username': request.user.username,
            'nombre': request.user.first_name, 'apellido': request.user.last_name,
            'email': request.user.email,
        })


class LogoutTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
