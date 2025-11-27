from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('process_frame/', views.process_frame, name='process_frame'),
    path('start_analyzing/', views.start_analyzing, name='start_analyzing'),
    path('qr/', views.qr_code_view, name='qr_code_view'),
]