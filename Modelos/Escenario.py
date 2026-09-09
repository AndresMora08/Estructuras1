from collections import deque
from datetime import datetime as Datetime
from typing import Dict, List, Optional
from AVL import AVL
from Estacion import Estacion
from Evento import Evento
from Zona import Zona


class Escenario:

    def __init__(
        self,
        zonas: Optional[List[Zona]] = None,
        estaciones: Optional[List[Estacion]] = None,
        reloj: Optional[Datetime] = None,
        arbol_avl: Optional[AVL] = None,
    ):
        self.zonas = zonas
        self.estaciones = estaciones
        self.reloj = reloj
        self.arbol_avl = arbol_avl
        self.cola_reportes = deque()
        self.historico: List[Evento] = []
        self.dict_eventos: Dict[int, Evento] = {}
        self.W: float = 48.0
        self.R: float = 40.0
        self.L: int = 3
        self.T: float = 72.0