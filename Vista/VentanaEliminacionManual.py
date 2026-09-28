import json
from typing import Callable, Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk, filedialog


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

    # Configuración de la ventana modal
    self.ventana = tk.Toplevel(parent_window)
    self.ventana.title("Gestión y Eliminación de Evento")
    self.ventana.geometry("380x320")
    self.ventana.resizable(False, False)
    self.ventana.grab_set()

    # Etiqueta principal con el ID del evento
    ttk.Label(
        self.ventana,
        text=f"Evento: SIS-{self.evento.id:06d}",
        font=("Arial", 11, "bold"),
    ).pack(pady=15)

    # Marco contenedor para los botones de acción
    f_acciones = ttk.Frame(self.ventana)
    f_acciones.pack(fill=tk.BOTH, expand=True, padx=20)

    # 1. BOTÓN ELIMINAR
    btn_eliminar = ttk.Button(
        f_acciones, text="🗑️ Eliminar Evento", command=self._ejecutar_eliminacion
    )
    btn_eliminar.pack(fill=tk.X, pady=8)

    # 2. BOTÓN GUARDAR JSON
    btn_guardar = ttk.Button(
        f_acciones, text="💾 Guardar en JSON", command=self.guardar_json
    )
    btn_guardar.pack(fill=tk.X, pady=8)

    # 3. BOTÓN CARGAR JSON
    btn_cargar = ttk.Button(
        f_acciones, text="📂 Cargar desde JSON", command=self.cargar_json
    )
    btn_cargar.pack(fill=tk.X, pady=8)

    # Botón inferior para cerrar o cancelar
    ttk.Button(
        self.ventana, text="Cancelar", command=self.ventana.destroy
    ).pack(pady=10)

  def _ejecutar_eliminacion(self):
    """Método para eliminar el evento del árbol AVL, diccionario y escenario."""
    # Cuadro de confirmación antes de borrar
    if not messagebox.askyesno(
        "Confirmar", 
        f"¿Está seguro de eliminar el evento SIS-{self.evento.id:06d}?", 
        parent=self.ventana
    ):
      return

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

  def guardar_json(self, ruta="sismolab_backup.json"):
    """Método para guardar los eventos actuales del diccionario en un archivo JSON."""
    try:
      datos_a_guardar = []
      for eid, ev in self.dict_eventos.items():
        datos_a_guardar.append({
            "id": getattr(ev, "id", eid),
            "clave": getattr(ev, "clave", None),
            "zona": str(getattr(ev, "zona", "Desconocida"))
        })

      with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos_a_guardar, archivo, indent=4, ensure_ascii=False)
      
      messagebox.showinfo(
          "Éxito", f"Datos guardados correctamente en {ruta}.", parent=self.ventana
      )
    except Exception as e:
      messagebox.showerror(
          "Error", f"No se pudo guardar el archivo:\n{e}", parent=self.ventana
      )

  def cargar_json(self):
    """Método para abrir un explorador de archivos y cargar registros JSON."""
    ruta = filedialog.askopenfilename(
        parent=self.ventana,
        title="Seleccionar archivo JSON",
        filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
    )
    if not ruta:
      return
    
    try:
      with open(ruta, "r", encoding="utf-8") as archivo:
        cargado = json.load(archivo)
        if isinstance(cargado, list):
          messagebox.showinfo(
              "Éxito", f"Archivo JSON cargado con éxito ({len(cargado)} registros leídos).", parent=self.ventana
          )
        else:
          messagebox.showwarning(
              "Advertencia", "El formato del JSON no corresponde a una lista válida.", parent=self.ventana
          )
    except Exception as e:
      messagebox.showerror(
          "Error", f"No se pudo leer el archivo JSON:\n{e}", parent=self.ventana
      )