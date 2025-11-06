from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('signup/', views.signup_api, name = 'signup_api'),
    path('login/', views.login_api, name = 'login_api'),
    path('logout/', views.logout_api, name = 'logout_api'),

    path('agregar_residuo/', views.agregar_residuo, name = 'agregar_residuo'),
    path('cant_por_tipo/', views.get_cant_por_tipo, name = 'cant_por_tipo'),
    path('puntos_usuario/', views.get_puntos_usuario, name = 'puntos_usuario'),
    path('ranking/', views.get_ranking, name = 'ranking'),
    path('ranking_por_tipo/', views.get_ranking_por_tipo, name = 'ranking_por_tipo'),

    path('ubicacion_estacion/', views.get_ubicacion_estacion, name = 'ubicacion_estacion'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]
