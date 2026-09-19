import tkinter as tk
from tkinter import ttk
from Modelos.AVL import AVL


class VisualizadorAVL:

  def __init__(self, root: tk.Tk, arbol_avl: AVL):
    self.ventana = tk.Toplevel(root)
    self.ventana.title("SismoLab AVL - Estructura del Árbol")
    self.ventana.geometry("900x600")

    self.arbol_avl = arbol_avl

    # Panel superior con controles
    frame_controles = ttk.Frame(self.ventana)
    frame_controles.pack(fill="x", padx=10, pady=5)

    btn_actualizar = ttk.Button(
        frame_controles, text="Actualizar Árbol", command=self.dibujar_arbol
    )
    btn_actualizar.pack(side=tk.LEFT, padx=5)

    # Lienzo de dibujo (Canvas)
    self.canvas = tk.Canvas(self.ventana, bg="white")
    self.canvas.pack(fill="both", expand=True)

    self.dibujar_arbol()

  def dibujar_arbol(self):
    self.canvas.delete("all")

    if self.arbol_avl is None or self.arbol_avl.raiz is None:
      self.canvas.create_text(
          450,
          300,
          text="[ El Árbol AVL está vacío ]",
          font=("Arial", 14, "bold"),
          fill="gray",
      )
      return

    ancho_canvas = max(self.ventana.winfo_width(), 900)
    x_inicial = ancho_canvas // 2
    y_inicial = 50

    self._dibujar_nodo(
        nodo=self.arbol_avl.raiz,
        x=x_inicial,
        y=y_inicial,
        desplazamiento_x=ancho_canvas // 4,
    )

  def _dibujar_nodo(self, nodo, x: int, y: int, desplazamiento_x: int):
    if nodo is None:
      return

    radio = 28
    distancia_y = 70

    # Dibujar conexión con el hijo izquierdo
    if nodo.izquierda:
      x_hijo = x - desplazamiento_x
      y_hijo = y + distancia_y
      self.canvas.create_line(x, y, x_hijo, y_hijo, fill="#555555", width=2)
      self._dibujar_nodo(
          nodo.izquierda, x_hijo, y_hijo, max(desplazamiento_x // 2, 30)
      )

    # Dibujar conexión con el hijo derecho
    if nodo.derecha:
      x_hijo = x + desplazamiento_x
      y_hijo = y + distancia_y
      self.canvas.create_line(x, y, x_hijo, y_hijo, fill="#555555", width=2)
      self._dibujar_nodo(
          nodo.derecha, x_hijo, y_hijo, max(desplazamiento_x // 2, 30)
      )

    # Dibujar figura del nodo
    self.canvas.create_oval(
        x - radio,
        y - radio,
        x + radio,
        y + radio,
        fill="#E1F5FE",
        outline="#0288D1",
        width=2,
    )

    # Muestra únicamente ID y Clave (Prioridad, Magnitud, ID)
    self.canvas.create_text(
        x,
        y - 6,
        text=f"ID: {nodo.evento.id}",
        font=("Arial", 9, "bold"),
        fill="#01579B",
    )
    self.canvas.create_text(
        x,
        y + 8,
        text=f"K: {nodo.clave}",
        font=("Arial", 8),
        fill="#333333",
    )