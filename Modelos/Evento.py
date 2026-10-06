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
        estado: str = "Pendiente",
        estado_catalogo: str = "Activo",  # <-- "Activo", "Archivado" or "Retirado"
        id_referencia = None,
        revision: int = 1  # <-- Receives revision with default value 1
    ):
        self.id = int(id_evento)
        self.magnitud = round(float(magnitud), 1)
        self.profundidad = round(float(profundidad), 1)
        self.epicentro = epicentro
        self.estacion_origen = estacion_origen

        # Initialize the list with the mandatory origin station
        self.estaciones = [estacion_origen.id_estacion] if estacion_origen else []

        # ISO 8601 date in UTC
        self.fecha_hora = (
            fecha_hora
            if fecha_hora
            else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        # Review/attention status
        self.revision = int(revision)
        self.estado = estado

        # Catalog lifecycle status ("Activo", "Archivado", "Retirado")
        self.estado_catalogo = estado_catalogo

        # Attribute for seismic association
        self.id_referencia = id_referencia

        # Priority and key for the AVL Tree
        self.prioridad = 0
        self.clave = (self.prioridad, self.magnitud, self.id)

        # Calculate the priority and insert the key
        self.calcular_prioridad()

        self.acceso_costoso = False

    @property
    def fecha(self) -> datetime:
        """
        Converts fecha_hora to a datetime object for association calculations.
        """
        if isinstance(self.fecha_hora, datetime):
            return self.fecha_hora
        try:
            return datetime.fromisoformat(self.fecha_hora.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                return datetime.strptime(self.fecha_hora, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                return datetime.utcnow()

    def actualizar_prioridad_y_clave(self, nueva_prioridad: int):
        self.prioridad = int(nueva_prioridad)
        self.clave = (self.prioridad, self.magnitud, self.id)

    def calcular_prioridad(self):
        es_poblada = (
            self.epicentro.zona.poblada
            if (self.epicentro and hasattr(self.epicentro, 'zona') and self.epicentro.zona)
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
                "x": self.epicentro.x if self.epicentro else None,
                "y": self.epicentro.y if self.epicentro else None,
                "zona_poblada": (
                    self.epicentro.zona.poblada 
                    if (self.epicentro and hasattr(self.epicentro, 'zona') and self.epicentro.zona) 
                    else False
                ),
            },
            "estacion_origen": self.estacion_origen.id_estacion if self.estacion_origen else None,
            "fecha_hora": self.fecha_hora,
            "revision": self.revision,
            "estado": self.estado,
            "estado_catalogo": self.estado_catalogo,
            "id_referencia": self.id_referencia,
            "estaciones": self.estaciones,
            "prioridad": self.prioridad,
            "clave": self.clave,
        }

    def evaluar_costo(self, profundidad_nodo: int, limite_L: int) -> None:
        if self.prioridad == 3 and profundidad_nodo > limite_L:
            self.acceso_costoso = True
        else:
            self.acceso_costoso = False