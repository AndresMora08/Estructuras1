
from Modelos.AVL import AVL
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class ControladorCorrecciones:

    def __init__(self, arbol_avl: AVL, dict_eventos: dict, escenario=None):
        self.arbol_avl = arbol_avl
        self.dict_eventos = dict_eventos
        self.escenario = escenario

    def verificacion_datos(self, evento_nuevo: Evento) -> bool:
        # Magnitude
        if not (-2.0 <= evento_nuevo.magnitud <= 10.0):
            return False
        if round(evento_nuevo.magnitud, 1) != evento_nuevo.magnitud:
            return False

        # Depth
        if not (0.0 <= evento_nuevo.profundidad <= 700.0):
            return False
        if round(evento_nuevo.profundidad, 1) != evento_nuevo.profundidad:
            return False

        # Epicenter Coordinates
        if evento_nuevo.epicentro is None:
            return False

        x, y = evento_nuevo.epicentro.x, evento_nuevo.epicentro.y

        if not (0.0 <= x <= 1000.0) or not (0.0 <= y <= 1000.0):
            return False

        if round(x, 1) != x or round(y, 1) != y:
            return False

        return True

    def correccion_manual(
        self, evento_nuevo: Evento, evento_viejo: Evento
    ) -> bool:

        # 1. Validate all resulting data before applying changes
        if not self.verificacion_datos(evento_nuevo):
            return False

        # 2. Recalculate priority and key of the new event
        evento_nuevo.calcular_prioridad()

        # 3. Increment revision and mark as pending
        evento_nuevo.revision = evento_viejo.revision + 1
        evento_nuevo.estado = "Pendiente"

        if hasattr(evento_viejo, "estaciones"):
            evento_nuevo.estaciones = list(evento_viejo.estaciones)

        clave_vieja = evento_viejo.clave
        clave_nueva = evento_nuevo.clave

        # 4. Case A: The key did not change
        if clave_nueva == clave_vieja:

            evento_viejo.profundidad = evento_nuevo.profundidad
            evento_viejo.epicentro = evento_nuevo.epicentro
            evento_viejo.fecha_hora = evento_nuevo.fecha_hora
            evento_viejo.revision = evento_nuevo.revision
            evento_viejo.estado = "Pendiente"
            evento_viejo.clave = clave_nueva

        # 5. Case B: The key changed
        else:

            if self.arbol_avl or getattr(
                    self.escenario,
                    "arbol_bst",
                    None
                ):

                limite_L = (
                    getattr(self.escenario, "L", 3)
                )

                # Remove from the AVL
                if self.arbol_avl is not None:
                    self.arbol_avl.eliminar(
                        clave_vieja,
                        limite_L
                    )

                # Remove from the BST
                if (
                    self.escenario is not None
                    and self.escenario.arbol_bst is not None
                ):
                    self.escenario.arbol_bst.eliminar(
                        clave_vieja,
                        limite_L
                    )

                # Insert into the AVL
                if self.arbol_avl is not None:
                    nuevo_nodo = Nodo(evento_nuevo)

                    self.arbol_avl.insertar(
                        nuevo_nodo,
                        limite_L
                    )

                # Insert into the BST
                if (
                    self.escenario is not None
                    and self.escenario.arbol_bst is not None
                ):
                    self.escenario.arbol_bst.insertar(
                        evento_nuevo,
                        limite_L
                    )

                # Update the reference in the dictionary
                self.dict_eventos[evento_viejo.id] = evento_nuevo

        return True