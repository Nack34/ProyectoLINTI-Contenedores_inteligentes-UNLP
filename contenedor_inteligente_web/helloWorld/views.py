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
    prediction_file = os.path.join(settings.MEDIA_ROOT, 'classified', '0', 'prediccion.txt')

    imagen_base = f'{base_dir}/foto_0.jpg'
    imagenes_objetos = []
    predicciones = []

    # Leer imágenes procesadas
    if os.path.exists(processed_dir):
        imagenes_objetos = [f'processed/0/{nombre}' for nombre in sorted(os.listdir(processed_dir)) 
                           if nombre.lower().endswith(('.jpg', '.png', '.jpeg'))]

    # Leer predicciones del archivo
    if os.path.exists(prediction_file):
        with open(prediction_file, 'r', encoding='utf-8') as f:
            predicciones = [line.strip() for line in f.readlines()]
    
    # Asegurarnos de que ambas listas tengan la misma longitud
    if len(imagenes_objetos) != len(predicciones):
        # Si hay diferencia, truncar la lista más larga
        min_length = min(len(imagenes_objetos), len(predicciones))
        imagenes_objetos = imagenes_objetos[:min_length]
        predicciones = predicciones[:min_length]

    objetos_y_predicciones = list(zip(imagenes_objetos, predicciones))
    
    context = {
        'imagen_base': imagen_base,
        'objetos_y_predicciones': objetos_y_predicciones
    }
    return render(request, 'ver_imagenes.html', context)