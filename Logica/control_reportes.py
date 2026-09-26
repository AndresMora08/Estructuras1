from Modelos.AVL import AVL
from Modelos.Escenario import Escenario
from Modelos.Evento import Evento
from Modelos.Reporte import Reporte
from Modelos.Estacion import Estacion
class ControladorReportes:
    
    def __init__(self,arbol_avl:AVL,escenario:Escenario):
        
        self.arbol_avl=arbol_avl
        self.escenario=escenario
        
    
    def verificacion_datos(self, evento_nuevo: Evento) -> bool:
    # Magnitud
     if not (-2.0 <= evento_nuevo.magnitud <= 10.0):
      return False
     if round(evento_nuevo.magnitud, 1) != evento_nuevo.magnitud:
      return False

    # Profundidad
     if not (0.0 <= evento_nuevo.profundidad <= 700.0):
        return False
     if round(evento_nuevo.profundidad, 1) != evento_nuevo.profundidad:
          return False

    # Coordenadas Epicentro
     if evento_nuevo.epicentro is None:
      return False

     x, y = evento_nuevo.epicentro.x, evento_nuevo.epicentro.y
     if not (0.0 <= x <= 1000.0) or not (0.0 <= y <= 1000.0):
      return False
     if round(x, 1) != x or round(y, 1) != y:
      return False

     return True

    def creacion_reporte(self, evento_viejo:Evento, evento_nuevo:Evento, estacion_emisora:Estacion )->bool:
        
        if  not self.verificacion_datos :
            return False
        
        
    
    