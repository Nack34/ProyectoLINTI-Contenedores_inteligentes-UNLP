from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, extend_schema_view
from api.serializers import (
    UserCreationSerializer, 
    LoginSerializer, 
    TokenSerializer,
    RefreshTokenSerializer,
    SuccessMessageSerializer,
    ErrorSerializer
)

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

def get_tokens_for_user(user):
    """
    Helper function to generate a new pair of access and refresh tokens
    for a given user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@extend_schema(
    summary = "Registrar un nuevo usuario",
    description = "Crea una nueva cuenta de usuario y devuelve tokens de acceso y refresco.",
    request = UserCreationSerializer,
    tags=['Autenticación'],
    responses={
        201: OpenApiResponse(
            response=TokenSerializer,
            description="Signup exitoso. Tokens de acceso y refresco.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Respuesta',
                    value={ 
                        'refresh': 'eyJhbGciOiJIUzI1NiI...',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGci...'
                     }
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Datos de usuario inválidos.",
            examples=[
                OpenApiExample(
                    'Error: Datos inválidos',
                    value={"error": "Datos de usuario inválidos."}
                )
            ]
        )
    },
    examples=[
         OpenApiExample(
            'Ejemplo de Petición',
            summary='Un usuario de prueba válido',
            value={
                'username': 'usuario_prueba',
                'password': 'pass123'
            },
            request_only=True,
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    """
    Registra un nuevo usuario.
    """
    serializer = UserCreationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response(TokenSerializer(tokens).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary = "Iniciar sesión (Login)",
    description = "Autentica a un usuario y devuelve sus tokens de acceso y refresco.",
    request = LoginSerializer,
    tags=['Autenticación'],

    responses={
        200: OpenApiResponse(
            response=TokenSerializer,
            description="Login exitoso. Token de acceso y refresco.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Respuesta',
                    value={ 
                        'refresh': 'eyJhbGciOiJIUzI1NiI...',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGci...'
                     }
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Datos de usuario inválidos.",
            examples=[
                OpenApiExample(
                    'Error: Datos inválidos',
                    value={"error": "Datos de usuario inválidos."}
                )
            ]
        )
    },

    examples=[
         OpenApiExample(
            'Ejemplo de Petición',
            summary='Un usuario de prueba válido',
            value={
                'username': 'usuario_prueba_1',
                'password': 'pass123'
            },
            request_only=True,
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Autentica un usuario existente.
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        # Obtenemos el usuario del serializer, que ya fue validado
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return Response(TokenSerializer(tokens).data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary = "Cerrar sesión (Logout)",
    description = "Invalida el token de refresco (refresh token) de un usuario para cerrar su sesión.",
    request = RefreshTokenSerializer,
    tags=['Autenticación'],
    responses={
        200: OpenApiResponse(
            response=SuccessMessageSerializer,
            description="Logout exitoso.",
            examples=[
                OpenApiExample(
                    "Respuesta Exitosa",
                    value={"message": "Logout exitoso."}
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Token inválido o no provisto.",
            examples=[
                OpenApiExample(
                    'Error: Token inválido o no provisto.',
                    value={"error": "Token inválido o no provisto."}
                )
            ]
        )
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_api(request):
    """
    Invalida un token de refresco (blacklist).
    """
    serializer = RefreshTokenSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh_token = serializer.validated_data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout exitoso.'}, status=status.HTTP_200_OK)
    except TokenError:
        return Response({'error': 'Token inválido o expirado.'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    post=extend_schema(
        summary="Refrescar Token",
        description="Obtiene un nuevo token de acceso (access token) enviando un token de refresco (refresh token) válido.",
        tags=['Autenticación'],
        request=TokenRefreshSerializer,
        responses={
            200: OpenApiResponse(
                description="Token refrescado exitosamente.",
                response=TokenRefreshSerializer,
                examples=[
                    OpenApiExample(
                        'Ejemplo de Respuesta',
                        value={'access': 'eyJhbGciOiJIUzI1NiI... (nuevo access token)'}
                    )
                ]
            ),
            401: OpenApiResponse(description="El token de refresco es inválido o ha expirado."),
        }
    )
)
class DecoratedTokenRefreshView(TokenRefreshView):
    pass