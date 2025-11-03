from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('signup/', views.signup_api, name = 'signup_api'),
    path('login/', views.login_api, name = 'login_api'),
    path('logout/', views.logout_api, name = 'logout_api'),
    path('agregar_residuo/', views.agregar_residuo, name = 'agregar_residuo'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]
