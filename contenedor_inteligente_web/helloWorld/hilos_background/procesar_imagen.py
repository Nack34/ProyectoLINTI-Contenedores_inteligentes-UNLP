import time
import cv2
import os
import time
import shutil
import sys

from .hilo_background import HiloBackground
from image_processing.recortar_objetos import recortar_img


class ProcesarImagen(HiloBackground):
    def __init__(self, guardar_multiples_fotos = False, dir_base = './pictures'):
        super().__init__()
        self.guardar_multiples_fotos = guardar_multiples_fotos
        self.dir_base = dir_base

    def capturar_imagen(self, cap, dir_img_base, i):
        i = i if self.guardar_multiples_fotos else 0
        ret, frame = cap.read()
        if ret:
            filename = f'{dir_img_base}/foto_{i}.jpg'
            cv2.imwrite(filename, frame)
            print(f"📸 Foto guardada en: {filename}")
        else:
            print("⚠️ No se pudo capturar la imagen")

    def procesar_img(self, dir_img_base, dir_img_processed, i):
        i = i if self.guardar_multiples_fotos else 0
        filename = f'{dir_img_base}/foto_{i}.jpg'
        dir_img_processed = f'{dir_img_processed}/{i}'

        # Si ya existe, lo borra con todo su contenido. Es necesario porque sino podrian quedar objetos viejos
        if os.path.exists(dir_img_processed):
            shutil.rmtree(dir_img_processed)

        # Crea el directorio vacío
        os.makedirs(dir_img_processed, exist_ok=True)

        recortar_img(filename, dir_img_processed)

    def run(self):
        print("🟢 Hilo 'Procesar Imagenes' iniciado")
        cap = cv2.VideoCapture(0)  # Usa la cámara por defecto. Esto despues cambiarlo para q sea la camara q se quiere

        dir_img_base = f'{self.dir_base}/base'
        dir_img_processed = f'{self.dir_base}/processed'
        os.makedirs(dir_img_base, exist_ok=True)  # Crea la carpeta si no existe
        os.makedirs(dir_img_processed, exist_ok=True)  # Crea la carpeta si no existe

        i = 0
        while self.running:
            print(f"Hilo 'Procesar Imagenes' ejecutándose por {i} vez")
            
            self.capturar_imagen(cap, dir_img_base, i)
            self.procesar_img(dir_img_base, dir_img_processed, i)
            
            i += 1
            time.sleep(1)

        cap.release()
        print("🔴 Hilo 'Procesar Imagenes' detenido")

