
class Zona:
    
    def __init__(
        self,
        nombre: str,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        poblada: bool,
    ):
        self.nombre = nombre
        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.poblada = poblada

    def contiene_punto(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max