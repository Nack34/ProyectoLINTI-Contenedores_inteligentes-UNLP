import threading
import time
import signal


class TestHilo():
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        print("🟢 Hilo iniciado")
        i = 0
        while self.running:
            print(f"Hilo ejecutándose por {i} vez")
            i += 1
            time.sleep(1)
        print("🔴 Hilo detenido")

    def stop(self):
        self.running = False
