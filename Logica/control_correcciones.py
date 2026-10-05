from Modelos.AVL import AVL
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class ControladorCorrecciones:

    def __init__(self, arbol_avl: AVL, dict_eventos: dict, escenario=None):
        self.arbol_avl = arbol_avl
        self.dict_eventos = dict_eventos
        self.escenario = escenario

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

    def correccion_manual(
        self, evento_nuevo: Evento, evento_viejo: Evento
    ) -> bool:

        # 1. Validar todos los datos resultantes antes de aplicar cambios
        if not self.verificacion_datos(evento_nuevo):
            return False

        # 2. Recalcular prioridad y clave del nuevo evento
        evento_nuevo.calcular_prioridad()

        # 3. Incrementar revisión y marcar como pendiente
        evento_nuevo.revision = evento_viejo.revision + 1
        evento_nuevo.estado = "Pendiente"

        if hasattr(evento_viejo, "estaciones"):
            evento_nuevo.estaciones = list(evento_viejo.estaciones)

        clave_vieja = evento_viejo.clave
        clave_nueva = evento_nuevo.clave

        # 4. Caso A: La clave no cambió
        if clave_nueva == clave_vieja:

            evento_viejo.profundidad = evento_nuevo.profundidad
            evento_viejo.epicentro = evento_nuevo.epicentro
            evento_viejo.fecha_hora = evento_nuevo.fecha_hora
            evento_viejo.revision = evento_nuevo.revision
            evento_viejo.estado = "Pendiente"
            evento_viejo.clave = clave_nueva

        # 5. Caso B: La clave cambió
        else:

            if self.arbol_avl or getattr(
                    self.escenario,
                    "arbol_bst",
                    None
                ):

                limite_L = (
                    getattr(self.escenario, "L", 3)
                )

                # Eliminar del AVL
                if self.arbol_avl is not None:
                    self.arbol_avl.eliminar(
                        clave_vieja,
                        limite_L
                    )

                # Eliminar del BST
                if (
                    self.escenario is not None
                    and self.escenario.arbol_bst is not None
                ):
                    self.escenario.arbol_bst.eliminar(
                        clave_vieja,
                        limite_L
                    )

                # Insertar en el AVL
                if self.arbol_avl is not None:
                    nuevo_nodo = Nodo(evento_nuevo)

                    self.arbol_avl.insertar(
                        nuevo_nodo,
                        limite_L
                    )

                # Insertar en el BST
                if (
                    self.escenario is not None
                    and self.escenario.arbol_bst is not None
                ):
                    self.escenario.arbol_bst.insertar(
                        evento_nuevo,
                        limite_L
                    )

                # Actualizar referencia en el diccionario
                self.dict_eventos[evento_viejo.id] = evento_nuevo

        return True