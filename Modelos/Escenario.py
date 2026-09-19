from collections import deque
from datetime import datetime as Datetime
from typing import Dict, List, Optional

from Modelos.AVL import AVL
from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Zona import Zona


class Escenario:

  def __init__(
      self,
      zonas: List[Zona] = [],
      estaciones: List[Estacion] = [],
      epicentros: List[Epicentro] = [],
      reloj: Optional[Datetime] = None,
      arbol_avl: Optional[AVL] = None,
  ):
    self.zonas: List[Zona] = zonas
    self.estaciones: List[Estacion] = estaciones
    self.epicentros: List[Epicentro] = epicentros

    self.reloj = reloj
    self.arbol_avl = arbol_avl
    self.cola_reportes = deque()
    self.historico: List[Evento] = []
    self.dict_eventos: Dict[int, Evento] = {}

    self.W: float = 48.0
    self.R: float = 40.0
    self.L: int = 3
    self.T: float = 72.0