import threading
import time
import signal

running = True

def procesar_fotos():
    print("🟢 Hilo iniciado")
    i = 0
    while running:
        print(f"Hilo ejecutándose por {i} vez")
        i += 1
        time.sleep(1)
    print("🔴 Hilo detenido")

def stop(*args):
    global running
    running = False
