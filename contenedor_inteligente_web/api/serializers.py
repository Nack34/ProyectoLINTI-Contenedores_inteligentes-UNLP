from rest_framework import serializers

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from api.models import Estacion

"""
  Autenticación
"""
class UserCreationSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar (signup) un nuevo usuario.
    Valida que el usuario no exista y que la contraseña sea fuerte.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
    )

    class Meta:
        model = User
        fields = ('username', 'password')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya existe.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    """
    Serializer para el login. Valida las credenciales.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if not user or not user.is_active:
            raise serializers.ValidationError("Credenciales incorrectas o usuario inactivo.")
        
        data['user'] = user
        return data

class TokenSerializer(serializers.Serializer):
    """
    Serializer para la RESPUESTA de los tokens.
    """
    refresh = serializers.CharField()
    access = serializers.CharField()

class RefreshTokenSerializer(serializers.Serializer):
    """
    Serializer para el REQUEST de logout.
    """
    refresh = serializers.CharField(required=True)

"""
  Residuos
"""
class SignedResiduoRequestSerializer(serializers.Serializer):
    """
    (Petición) Espera el ID firmado de un residuo, obtenido desde el QR.
    """
    id_residuo = serializers.CharField(
        help_text="El ID firmado del residuo, obtenido del código QR."
    )

class PuntosUsuarioSerializer(serializers.Serializer):
    """
    Serializer para devolver el total de puntos.
    """
    puntos = serializers.IntegerField(help_text="El total de puntos acumulados por el usuario.")

class TotalResiduosSerializer(serializers.Serializer):
    """
    Muestra la cantidad total de residuos reciclados por tipo.
    """
    nombre = serializers.CharField(help_text="El nombre del tipo de residuo (ej. Plastico).")
    cantidad = serializers.IntegerField(help_text="La cantidad total de veces que se recicló este tipo.")

class RankingEntrySerializer(serializers.Serializer):
    """
    Describe una entrada individual en la lista del ranking.
    """
    username = serializers.CharField(source='user__username')
    total_puntos = serializers.IntegerField()

class PosicionRankingSerializer(serializers.Serializer):
    """
    Devuelve la posición numérica en el ranking.
    """
    posicion = serializers.IntegerField(help_text="La posición del usuario en el ranking (1 es el mejor). 0 si no está en el ranking.")

"""
  Estaciones
"""
class EstacionSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Estacion.
    Define los campos que se mostrarán en la API.
    """
    class Meta:
        model = Estacion
        fields = ['id', 'nombre', 'latitud', 'longitud']

"""
  General
"""
class SuccessMessageSerializer(serializers.Serializer):
    """
    (Respuesta) Un mensaje de éxito genérico.
    """
    message = serializers.CharField()

class ErrorSerializer(serializers.Serializer):
    """
    Serializer genérico para respuestas de error (ej. 404, 400).
    """
    error = serializers.CharField(help_text="Descripción del error.")