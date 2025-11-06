import json
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Residuo, TipoResiduo, Estacion
from .decorators import jwt_required
from django.core.signing import Signer, BadSignature

from django.db import models

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

"""
    USUARIOS
"""
@csrf_exempt
def signup_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required.'}, status=400)
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Username already taken.'}, status=400)

            user = User.objects.create_user(username=username, password=password)
            
            tokens = get_tokens_for_user(user)
            return JsonResponse(tokens, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

@csrf_exempt
def login_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                tokens = get_tokens_for_user(user)
                return JsonResponse(tokens, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials.'}, status=400)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

@csrf_exempt
def logout_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refresh')

            token = RefreshToken(refresh_token)
            token.blacklist()
            return JsonResponse({'message': 'Successfully logged out.'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

"""
    RESIDUOS
"""
@csrf_exempt
@jwt_required
def agregar_residuo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_residuo = data.get('id_residuo')
            
            user = request.user 

            signer = Signer()
            id_residuo = signer.unsign(id_residuo)

            residuo = Residuo.objects.get(id=id_residuo)

            if residuo.user is not None:
                return JsonResponse({'error': 'Este residuo ya fue reclamado.'}, status=400)

            residuo.user = user
            residuo.save()
            
            return JsonResponse({'message': 'Residuo agregado correctamente.'}, status=200)
        
        except BadSignature:
            return JsonResponse({'error': 'ID de residuo inválido o manipulado.'}, status=400)
        except Residuo.DoesNotExist:
             return JsonResponse({'error': 'Residuo not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)

@csrf_exempt
@jwt_required
def get_puntos_usuario(request):
    if request.method == "GET":
        try:
            data = json.loads(request.body)
            id_user = data.get('id_user')
            
            if id_user is None:
                return JsonResponse({'error': 'ID de usuario is required.'}, status=400)
            
            user = User.objects.get(id=id_user)
            if user is None:
                return JsonResponse({'error': 'User not found.'}, status=404)
            
            puntos = Residuo.objects.filter(user=user)
            suma = puntos.aggregate(total_puntos=models.Sum('tipo_residuo__puntos'))
            total = suma['total_puntos'] or 0

            return JsonResponse({'puntos': total }, status=200)
        except Exception:
            return JsonResponse({'error': 'Internal server error.'}, status=500)

@csrf_exempt
@jwt_required
def get_cant_por_tipo(request):
    if request.method == "GET":
        try:
            data = list(
                TipoResiduo.objects
                    .annotate(cantidad=models.Count('residuo'))
                    .values('nombre', 'cantidad')
            )

            return JsonResponse({'ranking': data}, status=200)
        except Exception:
            return JsonResponse({'error': 'Internal server error.'}, status=500)    

@csrf_exempt
@jwt_required
def get_ranking(request):
    if request.method == "GET":
        try:
            ranking_residuo = list(
                Residuo.objects
                    .filter(user__isnull=False)
                    .values('user__username')
                    .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
                    .order_by('-total_puntos')[:10]
            )

            return JsonResponse({'ranking': ranking_residuo}, status=200)
        except Exception:
            return JsonResponse({'error': 'Internal server error.'}, status=500)

@csrf_exempt
@jwt_required
def get_ranking_por_tipo(request):
    if request.method == "GET":
        try:
            data = json.loads(request.body)
            tipo_residuo = data.get('tipo_residuo')
            if tipo_residuo is None:
                return JsonResponse({'error': 'Tipo de residuo is required.'}, status=400)
            
            ranking_residuo = list(
                Residuo.objects
                    .filter(tipo_residuo__nombre=tipo_residuo, user__isnull=False)
                    .values('user__username')
                    .annotate(total_puntos=models.Sum('tipo_residuo__puntos'))
                    .order_by('-total_puntos')[:10]
            )

            return JsonResponse({'ranking': ranking_residuo}, status=200)
        except Exception:
            return JsonResponse({'error': 'Internal server error.'}, status=500)

"""
    ESTACIONES
"""
@csrf_exempt
@jwt_required
def get_ubicacion_estacion(request):
    if request.method == "GET":
        try:
            data = json.loads(request.body)
            id_estacion = data.get('id_estacion')

            if id_estacion is None:
                return JsonResponse({'error': 'ID de estación is required.'}, status=400)
            
            estacion = Estacion.objects.get(id=id_estacion)
            return JsonResponse({'latitud': estacion.latitud, 'longitud': estacion.longitud}, status=200)
        except Estacion.DoesNotExist:
            return JsonResponse({'error': 'Estación not encontrada.'}, status=404)
        except Exception:
            return JsonResponse({'error': 'Internal server error.'}, status=500)