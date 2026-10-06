
from typing import List, Optional

from Modelos.Zona import Zona
class Epicentro:

    def __init__(self, x: float, y: float, zonas_escenario: List[Zona] = None):
        self.x = round(float(x), 1)
        self.y = round(float(y), 1)
        self.zona: Optional[Zona] = None

        if zonas_escenario:
            self.asignar_zona(zonas_escenario)

    def asignar_zona(self, zonas: List[Zona]) -> None:
    
        coincidentes = [z for z in zonas if z.contiene_punto(self.x, self.y)]

        if not coincidentes:
            self.zona = None
            return

        # If any of the matching zones is populated, it is selected
        zona_poblada = next((z for z in coincidentes if z.poblada), None)

        if zona_poblada:
            self.zona = zona_poblada
        else:
            self.zona = coincidentes[0]
        print(f"Epicentro en ({self.x}, {self.y}) asignado a zona: {self.zona.nombre}")

    @property
    def es_poblada(self) -> bool:
        """Allows directly checking whether the epicenter is populated without breaking if there is no zone."""
        return self.zona.poblada if self.zona else False

    def __repr__(self):
        return f"({self.x}, {self.y})"
