from typing import Callable, Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk


class VentanaEliminacionManual:

  def __init__(
      self,
      parent_window: tk.Toplevel,
      evento: object,
      arbol_avl: Optional[object],
      dict_eventos: Dict[int, object],
      escenario: object,
      callback_al_eliminar: Callable[[], None],
  ):
    self.evento = evento
    self.arbol_avl = arbol_avl
    self.dict_eventos = dict_eventos
    self.escenario = escenario
    self.callback_al_eliminar = callback_al_eliminar

    # Ventana modal simple
    self.ventana = tk.Toplevel(parent_window)
    self.ventana.title("Eliminar Evento")
    self.ventana.geometry("300x150")
    self.ventana.resizable(False, False)
    self.ventana.grab_set()

    # Mensaje de confirmación
    ttk.Label(
        self.ventana,
        text=f"¿Eliminar evento SIS-{self.evento.id:06d}?",
        font=("Arial", 10, "bold"),
    ).pack(pady=20)

    # Botones
    f_botones = ttk.Frame(self.ventana)
    f_botones.pack()

    ttk.Button(
        f_botones, text="Sí, Eliminar", command=self._ejecutar_eliminacion
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        f_botones, text="Cancelar", command=self.ventana.destroy
    ).pack(side=tk.LEFT, padx=5)

  def _ejecutar_eliminacion(self):
    try:
      # 1. Histórico
      if hasattr(self.escenario, "historico"):
        self.escenario.historico.append(self.evento)

      # 2. Árbol AVL
      if self.arbol_avl:
        self.arbol_avl.eliminar(self.evento.clave)

      # 3. Diccionario
      if self.evento.id in self.dict_eventos:
        del self.dict_eventos[self.evento.id]

      messagebox.showinfo(
          "Éxito", "Evento eliminado correctamente.", parent=self.ventana
      )
      self.ventana.destroy()
      self.callback_al_eliminar()

    except Exception as e:
      messagebox.showerror(
          "Error", f"No se pudo eliminar: {e}", parent=self.ventana
      )