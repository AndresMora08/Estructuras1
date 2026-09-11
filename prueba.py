from Modelos.Zona import Zona
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.AVL import AVL

arbol = AVL()

# 1. EVENTO Y NODO 1 (Prioridad 3, Magnitud 5.5) -> Clave: (3, 5.5, 1)
zona_ejemplo = Zona("Zona Centro", 0.0, 100.0, 0.0, 100.0, True)
epicentro_ejemplo = Epicentro(25.0, 50.0, [zona_ejemplo])

evento_ejemplo = Evento(1, 5.5, 12.0, epicentro_ejemplo, "2026-03-30 14:00:00")
evento_ejemplo.calcular_prioridad()
nodo1 = Nodo(evento_ejemplo)
arbol.insertar(nodo1)

# 2. EVENTO Y NODO 2 (Prioridad 3, Magnitud 6.5) -> Clave: (3, 6.5, 2)
zona_ejemplo2 = Zona("Zona Norte", 50.0, 150.0, 50.0, 150.0, False)
epicentro_ejemplo2 = Epicentro(75.0, 75.0, [zona_ejemplo2])

evento_ejemplo2 = Evento(2, 6.5, 20.0, epicentro_ejemplo2, "2026-03-30 15:00:00")
evento_ejemplo2.calcular_prioridad()
nodo2 = Nodo(evento_ejemplo2)
arbol.insertar(nodo2)

# 3. EVENTO Y NODO 3 (Prioridad 2, Magnitud 5.0) -> Clave: (2, 5.0, 3)
evento_ejemplo3 = Evento(3, 5.0, 40.0, epicentro_ejemplo2, "2026-03-30 16:00:00")
evento_ejemplo3.calcular_prioridad()
nodo3 = Nodo(evento_ejemplo3)
arbol.insertar(nodo3)

# 4. EVENTO Y NODO 4 (Prioridad 1, Magnitud 4.0) -> Clave: (1, 4.0, 4)
evento_ejemplo4 = Evento(4, 4.0, 50.0, epicentro_ejemplo2, "2026-03-30 17:00:00")
evento_ejemplo4.calcular_prioridad()
nodo4 = Nodo(evento_ejemplo4)
arbol.insertar(nodo4)

# 5. EVENTO Y NODO 5 (Prioridad 1, Magnitud 3.0) -> Clave: (1, 3.0, 5)
# Provoca el desbalance en el Nodo 3 y desencadena la rotación simple a la derecha
evento_ejemplo5 = Evento(5, 3.0, 50.0, epicentro_ejemplo2, "2026-03-30 18:00:00")
evento_ejemplo5.calcular_prioridad()
nodo5 = Nodo(evento_ejemplo5)
arbol.insertar(nodo5)

# Impresión del Árbol en consola
arbol.mostrar_arbol_consola()

#mostar altura de cada nodo
print(nodo1.altura)
print()
print(nodo2.altura)
print()
print(nodo3.altura)
print()
print(nodo4.altura)
print()
print(nodo5.altura)
print()
##prueba eliminacion
print("prueba eliminacion")
print()
print("Eliminando el nodo con clave:", evento_ejemplo4.clave)

arbol.eliminar(evento_ejemplo4.clave)
print()

arbol.mostrar_arbol_consola()
print()
print(nodo1.altura)
print()
print(nodo2.altura)
print()
print(nodo3.ver_info())
print()
print(nodo5.altura)