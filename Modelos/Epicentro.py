from typing import List, Optional

from Zona import Zona
class Epicentro:

    def __init__(self, x: float, y: float, zonas_escenario: List[Zona] = None):
        self.x = round(float(x), 1)
        self.y = round(float(y), 1)
        self.zona: Optional[Zona] = None

        if zonas_escenario:
            self.asignar_zona(zonas_escenario)

    def asignar_zona(self, zonas: List[Zona]) -> None:
        """Determina a qué zona pertenece el punto.

        Aplica la regla de desempate en bordes: si coincide con una poblada,
        prevalece.
        """
        coincidentes = [z for z in zonas if z.contiene_punto(self.x, self.y)]

        if not coincidentes:
            self.zona = None
            return

        # Si alguna de las zonas coincidentes es poblada, se queda con esa
        zona_poblada = next((z for z in coincidentes if z.poblada), None)

        if zona_poblada:
            self.zona = zona_poblada
        else:
            self.zona = coincidentes[0]

    @property
    def es_poblada(self) -> bool:
        """Facilita consultar directo si el epicentro es poblado sin romper si no hay zona."""
        return self.zona.poblada if self.zona else False

    def __repr__(self):
        return f"({self.x}, {self.y})"