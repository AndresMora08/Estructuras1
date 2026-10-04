import tkinter as tk


class VisualizadorAVL:
    """
    Draws the active AVL. It accepts either an AVL or the Escenario; with the
    scenario it always reads the LIVE tree (undo / restore replace the object).
    """

    def __init__(self, root: tk.Tk, fuente):
        self.ventana = tk.Toplevel(root)
        self.ventana.title("Visualizador Árbol AVL")
        self.ventana.geometry("900x600")

        self._fuente = fuente

        btn_actualizar = tk.Button(
            self.ventana,
            text="Actualizar Árbol",
            bg="#0288D1",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.dibujar_arbol,
        )
        btn_actualizar.pack(pady=10)

        self.canvas = tk.Canvas(self.ventana, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.dibujar_arbol()

    @property
    def arbol_avl(self):
        # An Escenario exposes 'arbol_avl'; an AVL instance does not
        return getattr(self._fuente, "arbol_avl", self._fuente)

    def dibujar_arbol(self):
        """Clears the canvas and draws from the root."""
        self.canvas.delete("all")
        arbol = self.arbol_avl

        if not arbol or not arbol.raiz:
            self.canvas.create_text(
                450, 250,
                text="El Árbol AVL está vacío",
                font=("Arial", 14, "bold"),
                fill="gray",
            )
            return

        self._dibujar_nodo(nodo=arbol.raiz, x=450, y=50, desplazamiento=200)

    def _dibujar_nodo(self, nodo, x: int, y: int, desplazamiento: int):
        """Recursive drawing: priority 3 is red fill, expensive access is a thick orange border."""
        if nodo is None:
            return

        radio = 25
        separacion_y = 60

        if nodo.izquierda:
            x_hijo = x - desplazamiento
            y_hijo = y + separacion_y
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill="gray", width=2)
            self._dibujar_nodo(nodo.izquierda, x_hijo, y_hijo, max(desplazamiento // 2, 30))

        if nodo.derecha:
            x_hijo = x + desplazamiento
            y_hijo = y + separacion_y
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill="gray", width=2)
            self._dibujar_nodo(nodo.derecha, x_hijo, y_hijo, max(desplazamiento // 2, 30))

        color_fondo = "#E1F5FE"
        color_borde = "#0288D1"
        grosor_borde = 2

        # Priority is shown with the fill color
        if nodo.evento.prioridad == 3:
            color_fondo = "#FFCDD2"
            color_borde = "#C62828"

        # Expensive access is shown ONLY with the border (never confused with priority)
        if getattr(nodo.evento, "acceso_costoso", False):
            color_borde = "#FF8F00"
            grosor_borde = 5

        self.canvas.create_oval(
            x - radio, y - radio, x + radio, y + radio,
            fill=color_fondo, outline=color_borde, width=grosor_borde
        )

        texto_nodo = f"ID: {nodo.evento.id}\nK: {nodo.clave}"
        self.canvas.create_text(
            x, y, text=texto_nodo, font=("Arial", 8, "bold"), fill="#212121"
        )