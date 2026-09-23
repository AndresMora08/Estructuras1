import tkinter as tk
from Modelos.AVL import AVL


class VisualizadorAVL:

    def __init__(self, root: tk.Tk, arbol_avl: AVL):
        # 1. Crear ventana modal sencilla
        self.ventana = tk.Toplevel(root)
        self.ventana.title("Visualizador Árbol AVL")
        self.ventana.geometry("900x600")

        self.arbol_avl = arbol_avl

        # 2. Botón de actualizar (Tkinter básico)
        btn_actualizar = tk.Button(
            self.ventana,
            text="Actualizar Árbol",
            bg="#0288D1",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.dibujar_arbol,
        )
        btn_actualizar.pack(pady=10)

        # 3. Lienzo de dibujo (Canvas)
        self.canvas = tk.Canvas(self.ventana, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Dibujar por primera vez
        self.dibujar_arbol()

    def dibujar_arbol(self):
        """Limpia la pantalla y empieza el dibujo desde la raíz."""
        self.canvas.delete("all")

        # Si el árbol está vacío, mostrar mensaje
        if not self.arbol_avl or not self.arbol_avl.raiz:
            self.canvas.create_text(
                450,
                250,
                text="El Árbol AVL está vacío",
                font=("Arial", 14, "bold"),
                fill="gray",
            )
            return

        # Dibujar a partir de la raíz en el centro del canvas
        self._dibujar_nodo(
            nodo=self.arbol_avl.raiz, x=450, y=50, desplazamiento=200
        )

    def _dibujar_nodo(self, nodo, x: int, y: int, desplazamiento: int):
        """Método recursivo sencillo para dibujar ramas y nodos."""
        if nodo is None:
            return

        radio = 25
        separacion_y = 60

        # --- DIBUJAR HIJO IZQUIERDO ---
        if nodo.izquierda:
            x_hijo = x - desplazamiento
            y_hijo = y + separacion_y
            # Línea de conexión
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill="gray", width=2)
            # Llamada recursiva
            self._dibujar_nodo(
                nodo.izquierda, x_hijo, y_hijo, max(desplazamiento // 2, 30)
            )

        # --- DIBUJAR HIJO DERECHO ---
        if nodo.derecha:
            x_hijo = x + desplazamiento
            y_hijo = y + separacion_y
            # Línea de conexión
            self.canvas.create_line(x, y, x_hijo, y_hijo, fill="gray", width=2)
            # Llamada recursiva
            self._dibujar_nodo(
                nodo.derecha, x_hijo, y_hijo, max(desplazamiento // 2, 30)
            )

        # --- DIBUJAR EL NODO (Círculo y Texto) ---
        # Círculo
        self.canvas.create_oval(
            x - radio,
            y - radio,
            x + radio,
            y + radio,
            fill="#E1F5FE",
            outline="#0288D1",
            width=2,
        )

        # Texto interno
        texto_nodo = f"ID: {nodo.evento.id}\nK: {nodo.clave}"
        self.canvas.create_text(
            x, y, text=texto_nodo, font=("Arial", 8, "bold"), fill="#01579B"
        )