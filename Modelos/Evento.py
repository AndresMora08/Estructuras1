from Epicentro import Epicentro
class Evento:

    def __init__(
        self,
        id,
        magnitud,
        profundidad,
        epicentro: Epicentro,
        fecha_hora,
        
    ):
        self.id = int(id)
        self.magnitud = round(float(magnitud), 1)
        self.profundidad = round(float(profundidad), 1)
        self.epicentro = (
            epicentro  # Objeto de tipo Epicentro (contiene x, y y zona)
        )
        self.fecha_hora = fecha_hora
        self.revision = 1
        self.estado = "Pendiente"
        self.estaciones = []
        self.prioridad = 0
        self.clave = (self.prioridad, self.magnitud, self.id)
        
        
        
    def actualizar_prioridad_y_clave(self, nueva_prioridad: int):
        self.prioridad = int(nueva_prioridad)
        self.clave = (self.prioridad, self.magnitud, self.id)
        
    def calcular_prioridad(self):
        if self.magnitud>=6.0 or (self.magnitud>=4.5 and self.profundidad<=30 and self.epicentro.zona.poblada):
            p=3
        elif self.magnitud>=4.5:
            p=2
        else:
           p=1
        self.actualizar_prioridad_y_clave(p)