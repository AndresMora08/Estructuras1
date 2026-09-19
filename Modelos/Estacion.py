from typing import Optional
from Modelos.Zona import Zona


class Estacion:

  def __init__(
      self,
      id_estacion: str,
      nombre: str,
      x: float,
      y: float,
      zona: Optional[Zona] = None,
  ):
    self.id_estacion = str(id_estacion).strip()
    self.nombre = str(nombre).strip()
    self.x = round(float(x), 1)
    self.y = round(float(y), 1)
    self.zona: Optional[Zona] = zona

    # Validamos inmediatamente si las coordenadas están dentro de la zona asignada
    if self.zona and not self.zona.contiene_punto(self.x, self.y):
      raise ValueError(
          f"Las coordenadas ({self.x}, {self.y}) están fuera de la zona"
          f" '{self.zona.nombre}'."
      )

  @property
  def es_poblada(self) -> bool:
    """Consulta si la estación pertenece a una zona poblada."""
    return self.zona.poblada if self.zona else False

  def __repr__(self):
    return f"Estacion({self.id_estacion}, '{self.nombre}', ({self.x}, {self.y}))"