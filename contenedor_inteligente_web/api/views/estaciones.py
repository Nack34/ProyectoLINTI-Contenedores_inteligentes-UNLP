from api.models import Estacion

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from api.serializers import EstacionSerializer, ErrorSerializer

@extend_schema(
    summary="Obtener lista de estaciones",
    operation_id="get_estaciones",
    description="Devuelve una lista de todas las estaciones de residuos disponibles.",
    tags=['Estaciones'],
    responses={
        200: EstacionSerializer(many=True)
    },
    examples=[
        OpenApiExample(
            'Ejemplo de respuesta',
            summary='Lista de estaciones de ejemplo',
            value=[
                {
                    "id": 1,
                    "nombre": "Estación Informática",
                    "latitud": -34.913,
                    "longitud": -57.9495
                },
                {
                    "id": 2,
                    "nombre": "Estación Bellas Artes",
                    "latitud": -34.915,
                    "longitud": -57.951
                }
            ],
            response_only=True,
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ubicacion_estaciones(request):
    """
    Devuelve una lista de todas las estaciones de residuos.
    """
    try:
        estaciones = Estacion.objects.all()
        serializer = EstacionSerializer(estaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {e}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Obtener detalles de una estación",
    operation_id="get_estacion",
    description="Devuelve la ubicación (latitud/longitud) y el nombre de una estación específica.",
    tags=['Estaciones'],
    parameters=[
        OpenApiParameter(
            name='id_estacion', 
            description='El ID de la estación a consultar.',
            required=True, 
            type=int,
            location=OpenApiParameter.PATH,
            examples=[
                OpenApiExample(
                    'Ejemplo de Estación 1',
                    summary='Consultar la Estación Informática',
                    value=1
                )
            ]
        )
    ],
    responses={
        200: OpenApiResponse(
            response=EstacionSerializer,
            description="Los detalles de la estación solicitada.",
            examples=[
                OpenApiExample(
                    'Respuesta de Ejemplo',
                    summary='Una estación de ejemplo',
                    value={
                        "id": 1,
                        "nombre": "Estación Informática",
                        "latitud": -34.913,
                        "longitud": -57.9495
                    }
                )
            ]
        ),
        404: OpenApiResponse(
            response=ErrorSerializer,
            description="Estación no encontrada.",
            examples=[
                OpenApiExample(
                    'Ejemplo de Error 404',
                    summary='ID de estación no existe',
                    value={
                        "error": "Estación no encontrada."
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ubicacion_estacion(request, id_estacion):
    """
    Devuelve los detalles de una estación específica por su ID.
    """
    try:
        estacion = Estacion.objects.get(id=id_estacion)
        serializer = EstacionSerializer(estacion)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Estacion.DoesNotExist:
        return Response(
            {'error': 'Estación no encontrada.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {e}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )