from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('start_analyzing', views.start_analyzing, name='start_analyzing'),
    path("qr/", views.qr_code_view, name="qr_code_view"),
    path("stream/result/", views.stream_result, name="stream_result"),
    path("stream/qr/", views.stream_qr, name="stream_qr"),
]
