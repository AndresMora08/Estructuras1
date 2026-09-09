
class Estacion:
    
    def __init__(self, id_estacion: str, nombre: str, x: float, y: float):
        self.id_estacion = str(id_estacion)
        self.nombre = nombre
        self.x = round(float(x), 1)
        self.y = round(float(y), 1)