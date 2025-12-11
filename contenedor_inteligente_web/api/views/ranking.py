from django.contrib.auth.models import User
from api.models import Residuo
from django.db import models
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from api.serializers import (
    ErrorSerializer,
    RankingEntrySerializer,
    PuntosUsuarioSerializer,
    PosicionRankingSerializer
)

@extend_schema(
    summary="Obtener puntos de usuario",
    description="Devuelve la suma total de puntos acumulados. Puedes consultar tus propios puntos (sin parámetros) o los de otro usuario pasando su ID.",
    tags=['Puntos'],
    parameters=[
        OpenApiParameter(
            name='id_user',
            description='(Opcional) ID del usuario a consultar. Si se omite, se usa el usuario autenticado.',
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Consultar otro usuario', value=5)]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=PuntosUsuarioSerializer,
            description="Total de puntos obtenido correctamente.",
            examples=[
                OpenApiExample(
                    'Respuesta Exitosa',
                    value={"puntos": 150}
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorSerializer,
            description="Usuario no encontrado.",
            examples=[OpenApiExample('Error', value={"error": "Usuario no encontrado."})]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer,
            description="ID inválido.",
            examples=[OpenApiExample('Error', value={"error": "ID de usuario inválido."})]
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
        id_user_param = request.query_params.get('id_user')

        if id_user_param:
            # Validamos que sea un número
            try:
                target_id = int(id_user_param)
                target_user = get_object_or_404(User, id=target_id)
            except ValueError:
                return Response({'error': 'ID de usuario inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Si no hay param, es el usuario logueado
            target_user = request.user

        resultado = target_user.residuo_set.aggregate(total=models.Sum('tipo_residuo__puntos'))
        
        # Si no tiene residuos devuelve None, lo convertimos a 0
        total_puntos = resultado['total'] or 0

        serializer = PuntosUsuarioSerializer({'puntos': total_puntos})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Http404:
        return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    summary="Obtener Ranking (Top 10)",
    description="Devuelve el top 10 de usuarios con más puntos. Opcionalmente se puede filtrar por tipo de residuo.",
    tags=['Ranking'],
    parameters=[
        OpenApiParameter(
            name='tipo_residuo', 
            description='(Opcional) Filtrar por tipo de residuo (ej. "Plastico", "Carton"). Si se omite, es el ranking global.', 
            required=False, 
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Filtrar', value='Plastico')]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=RankingEntrySerializer(many=True),
            description="Lista del Top 10.",
            examples=[
                OpenApiExample(
                    'Ranking Global',
                    value=[
                        {"username": "reciclador_pro", "total_puntos": 1500},
                        {"username": "eco_amigo", "total_puntos": 1200}
                    ]
                )
            ]
        ),
        400: OpenApiResponse(description="Parámetros inválidos.")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ranking(request):
    """
    Devuelve el top 10 de usuarios, opcionalmente filtrado por tipo.
    """
    try:
        tipo_residuo = request.query_params.get('tipo_residuo')

        if tipo_residuo is not None and tipo_residuo not in ['Plastico', 'Vidrio', 'Carton', 'Metal', 'Papel', 'Basura']:
            return Response({'error': 'El parámetro tipo_residuo es inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Residuo.objects.filter(user__isnull=False)

        if tipo_residuo:
            queryset = queryset.filter(tipo_residuo__nombre=tipo_residuo)

        ranking_data = (
            queryset
            .values(username=models.F('user__username'))
            .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
            .order_by('-total_puntos')[:10]
        )

        serializer = RankingEntrySerializer(ranking_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    summary="Obtener Ranking Semanal (Top 10)",
    description="Devuelve el top 10 de usuarios con más puntos en la semana actual (desde el lunes). Opcionalmente se puede filtrar por tipo de residuo.",
    tags=['Ranking'],
    parameters=[
        OpenApiParameter(
            name='tipo_residuo', 
            description='(Opcional) Filtrar por tipo de residuo (ej. "Plastico", "Carton"). Si se omite, es el ranking global semanal.', 
            required=False, 
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Filtrar', value='Plastico')]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=RankingEntrySerializer(many=True),
            description="Lista del Top 10 Semanal.",
            examples=[
                OpenApiExample(
                    'Ranking Semanal',
                    value=[
                        {"username": "reciclador_pro", "total_puntos": 300},
                        {"username": "eco_amigo", "total_puntos": 150}
                    ]
                )
            ]
        ),
        400: OpenApiResponse(description="Parámetros inválidos.")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ranking_semanal(request):
    """
    Devuelve el top 10 de usuarios de la semana actual.
    """
    try:
        tipo_residuo = request.query_params.get('tipo_residuo')

        if tipo_residuo is not None and tipo_residuo not in ['Plastico', 'Vidrio', 'Carton', 'Metal', 'Papel', 'Basura']:
            return Response({'error': 'El parámetro tipo_residuo es inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        queryset = Residuo.objects.filter(user__isnull=False, fecha_carga__gte=start_of_week)

        if tipo_residuo:
            queryset = queryset.filter(tipo_residuo__nombre=tipo_residuo)

        ranking_data = (
            queryset
            .values(username=models.F('user__username'))
            .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
            .order_by('-total_puntos')[:10]
        )

        serializer = RankingEntrySerializer(ranking_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    summary="Obtener Posición en Ranking",
    description="Devuelve la posición de un usuario específico en el ranking (Global o por Tipo).",
    tags=['Ranking'],
    parameters=[
        OpenApiParameter(
            name='id_usuario', 
            description='ID del usuario a buscar.', 
            required=True, 
            type=int,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('ID Usuario', value=5)]
        ),
        OpenApiParameter(
            name='tipo_residuo', 
            description='(Opcional) Filtrar por tipo de residuo.', 
            required=False, 
            type=str,
            location=OpenApiParameter.QUERY,
            examples=[OpenApiExample('Tipo', value='Plastico')]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=PosicionRankingSerializer,
            description="Posición encontrada.",
            examples=[
                OpenApiExample('Posición', value={"posicion": 5})
            ]
        ),
        400: OpenApiResponse(description="ID de usuario faltante o inválido.")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_posicion_ranking(request):
    """
    Calcula la posición de un usuario en el ranking.
    """
    try:
        id_user_str = request.query_params.get('id_usuario')
        tipo_residuo = request.query_params.get('tipo_residuo')

        if not id_user_str:
            return Response({'error': 'El parámetro id_usuario es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if tipo_residuo is not None and tipo_residuo not in ['Plastico', 'Vidrio', 'Carton', 'Metal', 'Papel', 'Basura']:
            return Response({'error': 'El parámetro tipo_residuo es inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_id = int(id_user_str)
        except ValueError:
            return Response({'error': 'ID de usuario inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            get_object_or_404(User, id=target_id)
        except Http404:
            return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Base Query
        queryset = Residuo.objects.filter(user__isnull=False)

        if tipo_residuo:
            queryset = queryset.filter(tipo_residuo__nombre=tipo_residuo)

        # Get full ordered list of User IDs
        ranking_ids = (
            queryset
            .values('user__id')
            .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
            .order_by('-total_puntos')
        )
        
        ordered_ids = [entry['user__id'] for entry in ranking_ids]

        if target_id in ordered_ids:
            posicion = ordered_ids.index(target_id) + 1
        else:
            posicion = 0

        serializer = PosicionRankingSerializer({'posicion': posicion})
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
