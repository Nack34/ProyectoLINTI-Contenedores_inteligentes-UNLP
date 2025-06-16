
from abc import ABC, abstractmethod

class HiloBackground(ABC):
    def __init__(self):
        super().__init__()
        self.running = True

    @abstractmethod
    def run(self):
        """Método que debe ser implementado por las subclases"""
        pass

    def stop(self):
        self.running = False