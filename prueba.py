from Modelos.Zona import Zona
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.AVL import AVL

arbol = AVL()

# 1. EVENTO Y NODO 1 (Prioridad 3)
zona_ejemplo = Zona("Zona Centro", 0.0, 100.0, 0.0, 100.0, True)
epicentro_ejemplo = Epicentro(25.0, 50.0, [zona_ejemplo])

evento_ejemplo = Evento(1, 5.5, 12.0, epicentro_ejemplo, "2026-03-30 14:00:00")
evento_ejemplo.calcular_prioridad()

# Creación explícita del Nodo e inserción
nodo1 = Nodo(evento_ejemplo)
arbol.insertar(nodo1)

# 2. EVENTO Y NODO 2 (Prioridad 3)
zona_ejemplo2 = Zona("Zona Norte", 50.0, 150.0, 50.0, 150.0, False)
epicentro_ejemplo2 = Epicentro(75.0, 75.0, [zona_ejemplo2])

evento_ejemplo2 = Evento(2, 6.5, 20.0, epicentro_ejemplo2, "2026-03-30 15:00:00")
evento_ejemplo2.calcular_prioridad()

# Creación explícita del Nodo e inserción
nodo2 = Nodo(evento_ejemplo2)
arbol.insertar(nodo2)

# 3. EVENTO Y NODO 3 (Prioridad 2)
evento_ejemplo3 = Evento(3, 5.0, 40.0, epicentro_ejemplo2, "2026-03-30 16:00:00")
evento_ejemplo3.calcular_prioridad()

# Creación explícita del Nodo e inserción
nodo3 = Nodo(evento_ejemplo3)
arbol.insertar(nodo3)

# Impresión del Árbol
arbol.mostrar_arbol_consola()

# Impresión de la información de todos los eventos
print("Información del Nodo1:")
print(nodo1.ver_info())
print()

print("Información del Nodo2:")
print(nodo2.ver_info())
print()

print("Información del Nodo3:")
print(nodo3.ver_info())
print()