from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings

def hello(requests):
    return render(requests, "home.html")
def world(requests):
    return render(requests, "world.html")


def ver_imagenes(request):
    base_dir = os.path.join(settings.MEDIA_ROOT, 'base')
    processed_dir = os.path.join(settings.MEDIA_ROOT, 'processed', '0')

    imagen_base = f'base/foto_0.jpg'
    imagenes_objetos = []

    if os.path.exists(processed_dir):
        for nombre in sorted(os.listdir(processed_dir)):
            if nombre.lower().endswith(('.jpg', '.png', '.jpeg')):
                imagenes_objetos.append(f'processed/0/{nombre}')

    context = {
        'imagen_base': imagen_base,
        'imagenes_objetos': imagenes_objetos
    }
    return render(request, 'ver_imagenes.html', context)