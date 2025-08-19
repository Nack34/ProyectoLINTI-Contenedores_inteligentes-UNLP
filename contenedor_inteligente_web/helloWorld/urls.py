from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name = 'hello'),
    path('world/', views.world, name = 'World'),
    path('ver_imagenes/', views.ver_imagenes, name='ver_imagenes'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('prender/<int:led_num>/', views.prender_led, name='prender_led'),
]
