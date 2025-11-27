# helloWorld/apps.py

import signal
import sys
import os
from django.apps import AppConfig

def shutdown_handler(signum, frame):
    """
    Gracefully shut down the camera when the server is stopped.
    """
    # We import here to avoid circular dependency issues
    from .views import camera_instance

    print("\nServer is shutting down. Releasing camera...")
    if camera_instance:
        # We need a way to properly release the camera.
        # Let's add a release() method to the VideoCamera class.
        camera_instance.release()
        print("Camera released. ✅")
    sys.exit(0)

class WebappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webapp'

    def ready(self):
        """
        This method is called when the app is ready.
        We set up the shutdown signal handler here.
        """
        # The RUN_MAIN check prevents this from running in the reloader process
        if os.environ.get('RUN_MAIN'):
            print("Setting up shutdown handler for the camera...")
            signal.signal(signal.SIGINT, shutdown_handler)
            signal.signal(signal.SIGTERM, shutdown_handler)