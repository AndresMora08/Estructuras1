from Modelos.AVL import AVL
from Modelos.Evento import Evento
class ControladorCorrecciones:

    def __init__(self,arbol_avl:AVL):
        self.arbol_avl = arbol_avl
        
    
    def correccion_manual(self, evento_nuevo: Evento, evento_viejo: Evento) -> bool:
        
        validacion = self.verificacion_datos(evento_nuevo)
        
        if validacion is False:
            return False
        
        
        evento_nuevo.calcular_prioridad()
        
    
        evento_nuevo.revision = evento_viejo.revision + 1
        evento_nuevo.estado = "Pendiente"
        
      
        evento_nuevo.estaciones = list(evento_viejo.estaciones)

        
        clave_vieja = evento_viejo.clave
        clave_nueva = evento_nuevo.clave

      
        if clave_nueva == clave_vieja:
         
            evento_viejo.profundidad = evento_nuevo.profundidad
            evento_viejo.epicentro = evento_nuevo.epicentro
            evento_viejo.fecha_hora = evento_nuevo.fecha_hora
            evento_viejo.revision = evento_nuevo.revision
            evento_viejo.estado = "Pendiente"
            evento_viejo.clave = clave_nueva
            
        else:
            
            self.arbol_avl.eliminar(clave_vieja)
            self.arbol_avl.insertar(clave_nueva)
        
        return True
            
            
        
    
    def verificacion_datos(evento_nuevo: Evento) -> bool:
      
        if not (-2.0 <= evento_nuevo.magnitud <= 10.0):
            return False
        if round(evento_nuevo.magnitud, 1) != evento_nuevo.magnitud:
            return False

        
        if not (0.0 <= evento_nuevo.profundidad <= 700.0):
            return False
        if round(evento_nuevo.profundidad, 1) != evento_nuevo.profundidad:
            return False

        
        x, y = evento_nuevo.epicentro.x, evento_nuevo.epicentro.y
        if not (0.0 <= x <= 1000.0) or not (0.0 <= y <= 1000.0):
            return False
        if round(x, 1) != x or round(y, 1) != y:
            return False
        
        return True