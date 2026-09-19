import tkinter as tk

# Importaciones de tu proyecto
from Modelos.AVL import AVL
from Modelos.Escenario import Escenario
from Vista.interfaz import SismoLabGUI


def main():
  # 1. Instanciar el árbol AVL
  arbol_avl = AVL()

  # 2. Instanciar el escenario pasando el árbol AVL y las listas iniciales
  escenario = Escenario(
      zonas=[], estaciones=[], epicentros=[], arbol_avl=arbol_avl
  )

  # 3. Inicializar la ventana de Tkinter
  root = tk.Tk()

  # 4. Iniciar la interfaz con el escenario enlazado
  app = SismoLabGUI(root=root, escenario=escenario)

  # 5. Bucle principal de ejecución
  root.mainloop()


if __name__ == "__main__":
  main()