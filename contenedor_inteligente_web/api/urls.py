from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    path('signup/', views.signup_api, name = 'signup_api'),
    path('login/', views.login_api, name = 'login_api'),
    path('logout/', views.logout_api, name = 'logout_api'),
    path('datos_usuario/', views.get_user_data, name = 'get_user_data'),

    path('residuo/reclamar/', views.reclamar_residuo, name = 'reclamar_residuo'),
    path('residuos/<int:id_usuario>/', views.total_residuos_por_usuario, name = 'total_residuos_por_usuario'),
    path('residuos/', views.total_residuos, name = 'total_residuos'),

    path('puntos/', views.get_puntos_usuario, name='puntos_usuario'),
    path('ranking/', views.get_ranking, name='ranking'),
    path('ranking/semanal/', views.get_ranking_semanal, name='ranking_semanal'),
    path('ranking/posicion/', views.get_posicion_ranking, name='posicion_ranking'),

    path('estaciones/<int:id_estacion>/', views.get_ubicacion_estacion, name='get_estacion'),
    path('estaciones/', views.get_ubicacion_estaciones, name='get_estaciones'),

    path('token/refresh/', views.DecoratedTokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
