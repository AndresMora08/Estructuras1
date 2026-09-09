from Epicentro import Epicentro
class Evento:

    def __init__(
        self,
        id,
        magnitud,
        profundidad,
        epicentro: Epicentro,
        fecha_hora,
        prioridad=1,
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
        self.prioridad = int(prioridad)
        self.clave = (self.prioridad, self.magnitud, self.id)
        
        
        
    def actualizar_prioridad_y_clave(self, nueva_prioridad: int):
        self.prioridad = int(nueva_prioridad)
        self.clave = (self.prioridad, self.magnitud, self.id)