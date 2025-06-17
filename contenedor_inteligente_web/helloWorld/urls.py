from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name = 'hello'),
    path('world/', views.world, name = 'World'),
    path('ver_imagenes/', views.ver_imagenes, name='ver_imagenes'),
]
