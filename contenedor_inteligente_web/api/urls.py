from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import views

urlpatterns = [
    path('signup/', views.signup_api, name = 'signup_api'),
    path('login/', views.login_api, name = 'login_api'),
    path('logout/', views.logout_api, name = 'logout_api'),

    path('agregar_residuo/', views.agregar_residuo, name = 'agregar_residuo'),
    path('total_residuos_por_usuario/', views.get_total_residuos_por_usuario, name = 'total_residuos_por_usuario'),
    path('puntos_usuario/', views.get_puntos_usuario, name = 'puntos_usuario'),

    path('total_residuos/', views.get_total_residuos, name = 'total_residuos'),
    path('ranking/', views.get_ranking, name = 'ranking'),
    path('ranking_por_tipo/', views.get_ranking_por_tipo, name = 'ranking_por_tipo'),
    path('posicion_ranking/', views.get_posicion_ranking, name = 'posicion_ranking'),
    path('posicion_ranking_por_tipo/', views.get_posicion_ranking_por_tipo, name = 'posicion_ranking_por_tipo'),

    path('estaciones/<int:id_estacion>/', views.get_ubicacion_estacion, name='get_estacion_detail'),
    path('estaciones/', views.get_ubicacion_estaciones, name='get_estaciones_list'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
