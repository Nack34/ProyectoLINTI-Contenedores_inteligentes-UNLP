from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken, InvalidToken
from django.contrib.auth.models import User

def jwt_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Obtener el token del header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'error': 'Authorization header required.'}, status=401)

        try:
            # 2. Extraer el token (ej. "Bearer <token>")
            token = auth_header.split(' ')[1]
            
            # 3. Validar el token y obtener el payload
            access_token = AccessToken(token)
            
            # Esta línea comprueba si el token es válido (firma y expiración)
            access_token.verify() 
            
            # 4. Obtener el usuario y adjuntarlo al request
            user_id = access_token.get('user_id')
            request.user = User.objects.get(id=user_id)
            
        except (InvalidToken, IndexError, User.DoesNotExist):
            return JsonResponse({'error': 'Invalid or expired token.'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=401)
        
        # 5. Si todo está bien, llamar a la vista original
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view