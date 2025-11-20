from django.contrib.auth.models import User
from api.models import Residuo

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from django.shortcuts import get_object_or_404
from api.serializers import (
    ErrorSerializer,
    RankingEntrySerializer,
    PuntosUsuarioSerializer,
    PosicionRankingSerializer
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import models

@extend_schema(
    summary="Obtener puntos de un usuario",
    description="Devuelve la suma total de puntos de los residuos reciclados por un usuario. "
                "Si no se especifica 'id_user', devuelve los puntos del usuario autenticado.",
    tags=['Ranking'],
    
    parameters=[
        OpenApiParameter(
            name='id_user', 
            description='(Opcional) El ID del usuario a consultar. Por defecto: el usuario actual.',
            required=True, 
            type=int,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Ejemplo', value=1)]
        )
    ],
    
    responses={
        200: OpenApiResponse(
            response=PuntosUsuarioSerializer,
            description="Total de puntos.",
            examples=[
                OpenApiExample(
                    'Respuesta Exitosa',
                    value={ "puntos": 150 }
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorSerializer, 
            description="Usuario no encontrado.",
            examples=[
                OpenApiExample(
                    'Error: No Encontrado',
                    value={"error": "Usuario no encontrado."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_puntos_usuario(request):
    """
    Calcula y devuelve los puntos totales de un usuario.
    """
    try:
        id_user = request.query_params.get('id_user')

        if id_user:
            # Si pidieron uno específico, lo buscamos (o devolvemos 404 si no existe)
            target_user = get_object_or_404(User, id=id_user)
        else:
            # Si no, usamos el usuario que está haciendo la petición
            target_user = request.user

        resultado = target_user.residuo_set.aggregate(total=models.Sum('tipo_residuo__puntos'))
        
        # Si no tiene residuos, la suma será None, así que devolvemos 0
        total_puntos = resultado['total'] or 0

        serializer = PuntosUsuarioSerializer({'puntos': total_puntos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ValueError:
        return Response({'error': 'ID de usuario inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener Ranking General (Top 10)",
    description="Devuelve una lista de los 10 usuarios con más puntos acumulados, ordenados de mayor a menor.",
    tags=['Ranking'],
    
    responses={
        200: OpenApiResponse(
            response=RankingEntrySerializer(many=True),
            description="Lista del Top 10 usuarios.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Ranking',
                    summary='Ranking actual',
                    description='Un ejemplo de cómo se ve la lista de usuarios y sus puntos.',
                    value=[
                        {"username": "reciclador_pro", "total_puntos": 1500},
                        {"username": "eco_amigo", "total_puntos": 1200},
                        {"username": "usuario_nuevo", "total_puntos": 350},
                        {"username": "test_user", "total_puntos": 100}
                    ]
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ranking(request):
    """
    Devuelve el top 10 de usuarios por puntos acumulados.
    """
    try:
        ranking_data = (
            Residuo.objects
            .filter(user__isnull=False)
            .values('user__username')
            .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
            .order_by('-total_puntos')[:10]
        )

        serializer = RankingEntrySerializer(ranking_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception:
        return Response({'error': 'Error interno del servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener Ranking por Tipo de Residuo (Top 10)",
    description="Devuelve el top 10 de usuarios que más puntos han sumado reciclando un tipo específico de residuo (ej. 'Plastico', 'Vidrio').",
    tags=['Ranking'],
    
    parameters=[
        OpenApiParameter(
            name='tipo_residuo', 
            description='El nombre del tipo de residuo por el cual filtrar (ej. "Plastico").',
            required=True, 
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Ejemplo de Tipo', value='Plastico')]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=RankingEntrySerializer(many=True),
            description="Lista del Top 10 para ese tipo de residuo.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Ranking de Plástico',
                    summary='Top recicladores de plástico',
                    value=[
                        {"username": "rey_del_plastico", "total_puntos": 500},
                        {"username": "eco_usuario", "total_puntos": 320},
                        {"username": "nuevo_user", "total_puntos": 45}
                    ]
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Parámetro 'tipo_residuo' faltante.",
            examples=[
                OpenApiExample(
                    'Error: Falta tipo de residuo',
                    value={"error": "Parámetro 'tipo_residuo' faltante."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ranking_por_tipo(request):
    """
    Devuelve el top 10 de usuarios para un tipo específico de residuo.
    """
    try:
        tipo_residuo = request.query_params.get('tipo_residuo')

        if not tipo_residuo:
            return Response({'error': 'El parámetro "tipo_residuo" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        ranking_data = (
            Residuo.objects
            .filter(
                tipo_residuo__nombre=tipo_residuo,
                user__isnull=False
            )
            .values('user__username')
            .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
            .order_by('-total_puntos')[:10]
        )

        serializer = RankingEntrySerializer(ranking_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception:
        return Response({'error': 'Error interno del servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener posición en el ranking global",
    description="Calcula la posición de un usuario específico en la tabla de líderes global basándose en sus puntos totales.",
    tags=['Ranking'],
    
    parameters=[
        OpenApiParameter(
            name='id_user', 
            description='El ID del usuario a buscar.',
            required=True, 
            type=int,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('ID de Ejemplo', value=5)]
        )
    ],
    
    responses={
        200: OpenApiResponse(
            response=PosicionRankingSerializer,
            description="Posición encontrada.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Posición',
                    summary='Usuario en el Top 3',
                    value={"posicion": 3}
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Parámetro 'id_user' faltante o inválido.",
            examples=[
                OpenApiExample(
                    'Error: ID faltante o inválido',
                    value={"error": "Parámetro 'id_user' faltante o inválido."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posicion_ranking(request):
    """
    Calcula la posición de un usuario en el ranking global.
    """
    try:
        id_user_str = request.query_params.get('id_user')

        if not id_user_str:
            return Response({'error': 'El parámetro "id_user" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            id_user = int(id_user_str)
        except ValueError:
            return Response({'error': 'ID inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        ranking_residuo = list(
            Residuo.objects
                .filter(user__isnull=False)
                .values('user__id')
                .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
                .order_by('-total_puntos')
        )

        pos = 0
        for i in range(len(ranking_residuo)):
            if ranking_residuo[i]['user__id'] == id_user:
                pos = i + 1
                break

        serializer = PosicionRankingSerializer({'posicion': pos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener posición en ranking por tipo",
    description="Calcula la posición de un usuario en la tabla de líderes para una categoría específica (ej. quién es el mejor reciclando 'Plastico').",
    tags=['Ranking'],
    
    parameters=[
        OpenApiParameter(
            name='id_user', 
            description='El ID del usuario.',
            required=True, 
            type=int,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('ID Usuario', value=5)]
        ),
        OpenApiParameter(
            name='tipo_residuo', 
            description='El nombre del tipo de residuo (ej. Plastico).',
            required=True, 
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Tipo Residuo', value='Plastico')]
        )
    ],
    
    responses={
        200: OpenApiResponse(
            response=PosicionRankingSerializer,
            description="Posición encontrada.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Posición',
                    summary='Usuario Top 1 en Plástico',
                    value={"posicion": 1}
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Parámetros faltantes o inválidos.",
            examples=[
                OpenApiExample(
                    'Error: parámetros faltantes o inválidos',
                    value={"error": "Parámetros faltantes o inválidos."}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posicion_ranking_por_tipo(request):
    """
    Calcula la posición de un usuario para un tipo específico de residuo.
    """
    try:
        id_user_str = request.query_params.get('id_user')
        tipo_residuo = request.query_params.get('tipo_residuo')

        if not id_user_str or not tipo_residuo:
            return Response({'error': 'Los parámetros "id_user" y "tipo_residuo" son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            id_user = int(id_user_str)
        except ValueError:
            return Response({'error': 'ID de usuario inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        ranking_residuo = list(
            Residuo.objects
                .filter(
                    tipo_residuo__nombre=tipo_residuo,
                    user__isnull=False
                )
                .values('user__id')
                .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
                .order_by('-total_puntos')
        )

        pos = 0
        for i in range(len(ranking_residuo)):
            if ranking_residuo[i]['user__id'] == id_user:
                pos = i + 1
                break

        serializer = PosicionRankingSerializer({'posicion': pos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno del servidor: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)