from django.contrib.auth.models import User
from api.models import Residuo, TipoResiduo
from django.core.signing import Signer, BadSignature

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from django.shortcuts import get_object_or_404
from django.http import Http404
from api.serializers import (
    SignedResiduoRequestSerializer,
    SuccessMessageSerializer,
    ErrorSerializer,
    TotalResiduosSerializer,
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import models

@extend_schema(
    summary="Reclamar un residuo",
    description="Asocia un residuo (creado por la estación) con el usuario "
                "autenticado que escaneó el código QR.",
    tags=['Residuos'],
    request=SignedResiduoRequestSerializer,
    examples=[
        OpenApiExample(
            'Petición de Ejemplo',
            summary='Un ID de residuo firmado',
            description='Un ID firmado de ejemplo, tal como vendría del QR.',
            value={
                "id_residuo": "1:1rG4b1:T_kG4... (ID firmado de ejemplo)" 
            },
            request_only=True
        )
    ],
    
    responses={
        200: OpenApiResponse(
            response=SuccessMessageSerializer,
            description="Residuo reclamado exitosamente.",
            examples=[
                OpenApiExample(
                    'Respuesta Exitosa',
                    value={"message": "Residuo agregado correctamente."}
                )
            ]
        ),
        400: OpenApiResponse(
            response=ErrorSerializer, 
            description="Error en la petición (JSON inválido, residuo ya reclamado, firma inválida).",
            examples=[
                OpenApiExample(
                    'Error: Ya Reclamado',
                    summary='El residuo ya tiene un usuario',
                    value={"error": "Este residuo ya fue reclamado."}
                ),
                OpenApiExample(
                    'Error: Firma Inválida',
                    summary='El ID fue manipulado o es incorrecto',
                    value={"error": "ID de residuo inválido o manipulado."}
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorSerializer, 
            description="Residuo no encontrado.",
            examples=[
                OpenApiExample(
                    'Error: No Encontrado',
                    value={"error": "Residuo no encontrado."}
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reclamar_residuo(request):
    """
    Asocia un residuo con un usuario, validando un ID firmado.
    """
    try:
        id_residuo_firmado = request.data.get('id_residuo')
        
        if id_residuo_firmado is None:
            return Response({'error': 'El campo "id_residuo" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user 
        signer = Signer()
        id_residuo = signer.unsign(id_residuo_firmado) # Esto devuelve el int (ej. 1)

        residuo = Residuo.objects.get(id=id_residuo)

        if residuo.user is not None:
            return Response({'error': 'Este residuo ya fue reclamado.'}, status=status.HTTP_400_BAD_REQUEST)

        residuo.user = user
        residuo.save()
        
        return Response({'message': 'Residuo agregado correctamente.'}, status=status.HTTP_200_OK)
    
    except BadSignature:
        return Response({'error': 'ID de residuo inválido o manipulado.'}, status=status.HTTP_400_BAD_REQUEST)
    except Residuo.DoesNotExist:
         return Response({'error': 'Residuo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Error interno del servidor: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener totales por tipo de residuo",
    operation_id="get_residuos",
    description="Devuelve una lista con la cantidad total de residuos reciclados para cada categoría.",
    tags=['Residuos'],
    responses={
        200: OpenApiResponse(
            response=TotalResiduosSerializer(many=True),
            description="Lista de conteos por tipo.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Totales',
                    summary='Totales de reciclaje',
                    value=[
                        {"nombre": "Plastico", "cantidad": 150},
                        {"nombre": "Vidrio", "cantidad": 80},
                        {"nombre": "Carton", "cantidad": 45},
                        {"nombre": "Metal", "cantidad": 20},
                        {"nombre": "Papel", "cantidad": 100},
                        {"nombre": "Basura", "cantidad": 10}
                    ]
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_residuos(request):
    """
    Cuenta cuántos residuos hay de cada tipo en la base de datos.
    """
    try:
        data = TipoResiduo.objects.annotate(cantidad=models.Count('residuo')).order_by('-cantidad')

        serializer = TotalResiduosSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Obtener totales de residuos por usuario",
    operation_id="get_residuos_por_usuario",
    description="Devuelve una lista con la cantidad de residuos reciclados por un usuario específico, desglosado por tipo.",
    tags=['Residuos'],
    parameters=[
        OpenApiParameter(
            name='id_usuario',
            description='El ID del usuario a consultar.',
            required=True,
            type=int,
            location=OpenApiParameter.PATH,
            examples=[OpenApiExample('ID Usuario', value=5)]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=TotalResiduosSerializer(many=True),
            description="Lista de conteos por tipo.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Respuesta',
                    summary='Totales del usuario',
                    value=[
                        {"nombre": "Plastico", "cantidad": 12},
                        {"nombre": "Vidrio", "cantidad": 0},
                        {"nombre": "Carton", "cantidad": 8},
                        {"nombre": "Metal", "cantidad": 20},
                        {"nombre": "Papel", "cantidad": 0},
                        {"nombre": "Basura", "cantidad": 10}
                    ]
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorSerializer,
            description="Usuario no encontrado.",
            examples=[OpenApiExample('Error', value={"error": "Usuario no encontrado."})]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def total_residuos_por_usuario(request, id_usuario):
    """
    Devuelve la cantidad de residuos por tipo para un usuario específico.
    """
    try:
        target_user = get_object_or_404(User, id=id_usuario)
        
        data = (
            TipoResiduo.objects
            .annotate(cantidad=models.Count('residuo', filter=models.Q(residuo__user=target_user)))
            .values('nombre', 'cantidad')
            .order_by('-cantidad')
        )

        serializer = TotalResiduosSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Http404:
        return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Error interno: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)