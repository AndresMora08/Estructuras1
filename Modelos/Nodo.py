from dataclasses import dataclass
from typing import Optional
from .Evento import Evento
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
    
    def ver_info(self):
        return {
            "evento": self.evento.ver_info(),
            "izquierda": self.izquierda.ver_info() if self.izquierda else None,
            "derecha": self.derecha.ver_info() if self.derecha else None,
            "altura": self.altura
        }
        
    def es_hoja(self) -> bool:
        return self.izquierda is None and self.derecha is None
    
    def tiene_hijo_izquierdo(self) -> bool:
        return self.izquierda is not None
    
    def tiene_hijo_derecho(self) -> bool:
        return self.derecha is not None
    def tiene_dos_hijos(self) -> bool:
        return self.izquierda is not None and self.derecha is not None