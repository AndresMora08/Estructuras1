from dataclasses import dataclass
from typing import Optional
from Evento import Evento
@dataclass
class Nodo:
    evento:Evento
    izquierda: Optional['Nodo'] = None
    derecha: Optional['Nodo'] = None
    altura: int = 1
    
    @property
    def clave(self) -> tuple:
        return self.evento.clave
    
    def actualizar_altura(self):
        altura_izquierda = self.izquierda.altura if self.izquierda else 0
        altura_derecha = self.derecha.altura if self.derecha else 0
        self.altura = 1 + max(altura_izquierda, altura_derecha)
        
    @property
    def obtener_altura(self) -> int:
        return self.altura