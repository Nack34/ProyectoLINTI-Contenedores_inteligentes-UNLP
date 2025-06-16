import time
from .hilo_background import HiloBackground

class TestHilo(HiloBackground):
    def run(self):
        print("🟢 Hilo Test iniciado")
        i = 0
        while self.running:
            print(f"Hilo Test ejecutándose por {i} vez")
            i += 1
            time.sleep(1)
        print("🔴 Hilo Test detenido")

