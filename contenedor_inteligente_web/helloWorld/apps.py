from django.apps import AppConfig
import threading
import signal
import os
from .test_hilos import test_hilo

class HelloworldConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'helloWorld'

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
            
            # Iniciar el thread como no-daemon
            self.thread = threading.Thread(target=test_hilo.procesar_fotos)
            self.thread.daemon = False  # IMPORTANTE: debe ser False para usar join()
            self.thread.start()

    def handle_exit(self, signum, frame):
        print(f"\nRecibida señal {signum}, deteniendo hilo...")
        
        # Solicitar detención al hilo
        test_hilo.stop()
        
        # Esperar máximo 3 segundos a que termine
        self.thread.join(timeout=3.0)
        
        if self.thread.is_alive():
            print("⚠️ hilo no terminó a tiempo, forzando salida")
        else:
            print("✅ hilo detenido correctamente")
        
        # Restaurar manejadores originales y terminar
        signal.signal(signal.SIGINT, self.original_handlers[signal.SIGINT])
        signal.signal(signal.SIGTERM, self.original_handlers[signal.SIGTERM])
        
        # Ejecutar el manejador original de Django
        self.original_handlers[signum](signum, frame)