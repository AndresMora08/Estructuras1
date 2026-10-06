from Modelos.Evento import Evento
from Modelos.Estacion import Estacion

class Reporte:
    
    def __init__(self, evento: Evento, estacion_emisora: Estacion, revision: int):
        self.evento = evento
        self.estacion_emisora = estacion_emisora
        self.revision = revision
    
    @property
    def id_evento(self) -> int:
     
        return self.evento.id