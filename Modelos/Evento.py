class Evento:
    def __init__(self, id, magnitud, profundidad, epicentro, fecha_hora):
        self.id = int(id)
        self.magnitud = round(float(magnitud), 1)
        self.profundidad = round(float(profundidad), 1)
        self.epicentro = (round(float(epicentro[0]), 1), round(float(epicentro[1]), 1))
        self.fecha_hora = fecha_hora
        self.revision = 1
        self.estado = "Pendiente"
        self.estaciones = []
        self.prioridad = 0
        self.clave = (self.prioridad, self.magnitud, self.id)
        
    def actualizar_prioridad_y_clave(self, nueva_prioridad: int):
        self.prioridad = int(nueva_prioridad)
        self.clave = (self.prioridad, self.magnitud, self.id)