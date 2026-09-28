from typing import Callable, Dict, Optional
import json
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

    # Ventana modal un poco más amplia para acomodar los nuevos botones de JSON
    self.ventana = tk.Toplevel(parent_window)
    self.ventana.title("Gestión y Eliminación de Evento")
    self.ventana.geometry("380x260")
    self.ventana.resizable(False, False)
    self.ventana.grab_set()

    # Mensaje de confirmación original
    ttk.Label(
        self.ventana,
        text=f"¿Eliminar evento SIS-{self.evento.id:06d}?",
        font=("Arial", 10, "bold"),
    ).pack(pady=15)

    # Botones originales de acción (Sí, Eliminar / Cancelar)
    f_botones = ttk.Frame(self.ventana)
    f_botones.pack(pady=5)

    ttk.Button(
        f_botones, text="Sí, Eliminar", command=self._ejecutar_eliminacion
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        f_botones, text="Cancelar", command=self.ventana.destroy
    ).pack(side=tk.LEFT, padx=5)

    # Separador visual
    ttk.Separator(self.ventana, orient="horizontal").pack(fill="x", padx=20, pady=15)

    # Sección de respaldo / gestión JSON
    ttk.Label(
        self.ventana,
        text="Gestión de Datos (JSON)",
        font=("Arial", 9, "italic"),
    ).pack(pady=2)

    f_json = ttk.Frame(self.ventana)
    f_json.pack(pady=5)

    ttk.Button(
        f_json, text="Guardar JSON", command=self.guardar_json
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        f_json, text="Cargar JSON", command=self.cargar_json
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

  def guardar_json(self, ruta="sismolab_backup.json"):
    """Método para guardar los eventos actuales del diccionario en un archivo JSON."""
    try:
      # Convertimos el diccionario de eventos a una lista serializable si es necesario, 
      # o guardamos las propiedades clave de los eventos recolectados.
      datos_a_guardar = []
      for eid, ev in self.dict_eventos.items():
        # Intentamos extraer atributos comunes del evento de forma segura
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
    """Método para cargar datos externos desde un archivo JSON."""
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