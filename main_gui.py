import tkinter as tk
from Modelos.AVL import AVL
from Modelos.BST import ArbolBST
from Modelos.Escenario import Escenario
from Vista.interfaz import SismoLabGUI


def main():
    arbol_avl = AVL()
    arbol_bst = ArbolBST()

    escenario = Escenario(
        zonas=[],
        estaciones=[],
        epicentros=[],
        arbol_avl=arbol_avl,
        arbol_bst=arbol_bst
    )

    root = tk.Tk()
    app = SismoLabGUI(
        root=root,
        escenario=escenario
    )
    root.mainloop()


if __name__ == "__main__":
    main()