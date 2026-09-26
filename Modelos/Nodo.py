from dataclasses import dataclass
from typing import Optional
from Modelos.Evento import Evento

@dataclass
class Nodo:
    evento:Evento
    izquierda: Optional['Nodo'] = None
    derecha: Optional['Nodo'] = None
    altura: int = 1
    profundidad=int=0
    
    @property
    def clave(self) -> tuple:
        return self.evento.clave
    
    def actualizar_altura(self):
        altura_izquierda = self.izquierda.altura if self.izquierda else 0
        altura_derecha = self.derecha.altura if self.derecha else 0
        self.altura = 1 + max(altura_izquierda, altura_derecha)
    

    def actualizar_profundidad_y_costo(self, prof_actual, limite_L) -> None:
        self.profundidad = prof_actual
        if self.evento:
            self.evento.evaluar_costo(self.profundidad, limite_L)
        
    @property
    def obtener_altura(self):
        return self.altura
    
    def ver_info(self):
        return {
            "evento": self.evento.ver_info(),
            "izquierda": self.izquierda.ver_info() if self.izquierda else None,
            "derecha": self.derecha.ver_info() if self.derecha else None,
            "altura": self.altura,
            "profundidad":self.profundidad
        }
        
    def es_hoja(self) -> bool:
        return self.izquierda is None and self.derecha is None
    
    def tiene_hijo_izquierdo(self) -> bool:
        return self.izquierda is not None
    
    def tiene_hijo_derecho(self) -> bool:
        return self.derecha is not None
        
    def tiene_dos_hijos(self) -> bool:
        return self.izquierda is not None and self.derecha is not None