from django.apps import AppConfig
from django.conf import settings 
import threading
import signal
import os
from .test_hilos.test_hilo import TestHilo

class HelloworldConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloWorld'
    
    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.tareas = [TestHilo(), TestHilo()]
        self.threads = []
        self.original_handlers = {}

    def init_thread(self, to_thread):
        t = threading.Thread(target=to_thread.run)
        t.start()
        self.threads.append(t)

    def ready(self):
        # Solo en proceso principal (evita doble ejecución en desarrollo)
        if os.environ.get('RUN_MAIN') == 'true' or not settings.DEBUG:
            # Configurar manejo de señales
            self.original_handlers = {
                signal.SIGINT: signal.getsignal(signal.SIGINT),
                signal.SIGTERM: signal.getsignal(signal.SIGTERM)
            }
            
            signal.signal(signal.SIGINT, self.handle_exit)
            signal.signal(signal.SIGTERM, self.handle_exit)
            
            for script in self.tareas:
                self.init_thread(script)


    def handle_exit(self, signum, frame):
        print(f"\nRecibida señal {signum}, deteniendo hilos...")
        
        # Parar hilos
        for tarea in self.tareas:
            tarea.stop()

        # Esperar máximo 3 segundos a que terminen
        for idx, t in enumerate(self.threads):
            t.join(timeout=3.0)
            if t.is_alive():
                print(f"⚠️ Hilo #{idx} no terminó a tiempo")
            else:
                print(f"✅ Hilo #{idx} detenido")

        # Restaurar manejadores originales y terminar
        signal.signal(signal.SIGINT, self.original_handlers[signal.SIGINT])
        signal.signal(signal.SIGTERM, self.original_handlers[signal.SIGTERM])
        
        # Ejecutar el manejador original de Django
        if callable(self.original_handlers[signum]):
            self.original_handlers[signum](signum, frame)