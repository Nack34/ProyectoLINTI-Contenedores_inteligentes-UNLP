from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name = 'hello'),
    path('world/', views.world, name = 'World'),
    path('ver_imagenes/', views.ver_imagenes, name='ver_imagenes'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('prender/<int:led_num>/', views.prender_led, name='prender_led'),
    path('start_analyzing', views.start_analyzing, name='start_analyzing'),
    path("qr/", views.qr_code_view, name="qr_code_view"),
    path("stream/result/", views.stream_result, name="stream_result"),
    path("stream/qr/", views.stream_qr, name="stream_qr"),
]
