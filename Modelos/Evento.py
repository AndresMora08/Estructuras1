from datetime import datetime
from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion


class Evento:

  def __init__(
      self,
      id_evento: int,
      magnitud: float,
      profundidad: float,
      epicentro: Epicentro,
      estacion_origen: Estacion,
      fecha_hora: str = None,
  ):
    self.id = int(id_evento)
    self.magnitud = round(float(magnitud), 1)
    self.profundidad = round(float(profundidad), 1)
    self.epicentro = epicentro
    self.estacion_origen = estacion_origen

    # Inicializa la lista con la estación origen obligatoria
    self.estaciones = [estacion_origen.id_estacion]

    # Fecha ISO 8601 en UTC
    self.fecha_hora = (
        fecha_hora
        if fecha_hora
        else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    # Valores por defecto del sistema
    self.revision = 1
    self.estado = "Pendiente"

    # Prioridad y Clave para el Árbol AVL
    self.prioridad = 0
    self.clave = (self.prioridad, self.magnitud, self.id)

    # Calcula la prioridad e inserta la clave
    self.calcular_prioridad()

  def actualizar_prioridad_y_clave(self, nueva_prioridad: int):
    self.prioridad = int(nueva_prioridad)
    self.clave = (self.prioridad, self.magnitud, self.id)

  def calcular_prioridad(self):
    es_poblada = (
        self.epicentro.zona.poblada
        if (self.epicentro and self.epicentro.zona)
        else False
    )

    if self.magnitud >= 6.0 or (
        self.magnitud >= 4.5 and self.profundidad <= 30.0 and es_poblada
    ):
      p = 3
    elif self.magnitud >= 4.5:
      p = 2
    else:
      p = 1

    self.actualizar_prioridad_y_clave(p)

  def ver_info(self):
    return {
        "id": self.id,
        "magnitud": self.magnitud,
        "profundidad": self.profundidad,
        "epicentro": {
            "x": self.epicentro.x,
            "y": self.epicentro.y,
            "zona_poblada": (
                self.epicentro.zona.poblada if self.epicentro.zona else False
            ),
        },
        "estacion_origen": self.estacion_origen.id_estacion,
        "fecha_hora": self.fecha_hora,
        "revision": self.revision,
        "estado": self.estado,
        "estaciones": self.estaciones,
        "prioridad": self.prioridad,
        "clave": self.clave,
    }