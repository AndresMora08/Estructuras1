import tkinter as tk
from tkinter import messagebox, ttk

# Importaciones de tu proyecto
from Modelos.Epicentro import Epicentro
from Modelos.Escenario import Escenario
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.Zona import Zona
from Vista.VisualizadorAVL import VisualizadorAVL


class SismoLabGUI:

  def __init__(self, root: tk.Tk, escenario: Escenario):
    self.root = root
    self.escenario = escenario

    # Configuración de la ventana principal
    self.root.title("SismoLab AVL - Monitor")
    self.root.geometry("850x500")

    # Componentes base
    self._agregar_mensaje_prueba()
    self._agregar_botones()

  def _agregar_mensaje_prueba(self):
    etiqueta = ttk.Label(
        self.root, text="¡Bienvenido a SismoLab AVL!", font=("Arial", 14, "bold")
    )
    etiqueta.pack(pady=20)

  def _agregar_botones(self):
    frame_botones = ttk.Frame(self.root)
    frame_botones.pack(pady=10)

    btn_zona = ttk.Button(
        frame_botones, text="Crear Zona", command=self._abrir_formulario_zona
    )
    btn_zona.pack(side=tk.LEFT, padx=5)

    btn_estacion = ttk.Button(
        frame_botones,
        text="Crear Estación",
        command=self._abrir_formulario_estacion,
    )
    btn_estacion.pack(side=tk.LEFT, padx=5)

    btn_epicentro = ttk.Button(
        frame_botones,
        text="Crear Epicentro",
        command=self._abrir_formulario_epicentro,
    )
    btn_epicentro.pack(side=tk.LEFT, padx=5)

    btn_evento = ttk.Button(
        frame_botones, text="Crear Evento", command=self._abrir_formulario_evento
    )
    btn_evento.pack(side=tk.LEFT, padx=5)

    # Botón para abrir el visualizador gráfico del Árbol AVL
    btn_ver_arbol = ttk.Button(
        frame_botones,
        text="Ver Árbol AVL",
        command=self._abrir_visualizador_arbol,
    )
    btn_ver_arbol.pack(side=tk.LEFT, padx=5)

  def _abrir_visualizador_arbol(self):
    if (
        getattr(self.escenario, "arbol_avl", None) is None
        or self.escenario.arbol_avl.raiz is None
    ):
      messagebox.showinfo(
          "Árbol Vacío",
          "El árbol AVL no contiene eventos registrados aún.",
          parent=self.root,
      )
      return
    VisualizadorAVL(self.root, self.escenario.arbol_avl)

  # ------------------------------------------------------------------
  # FORMULARIO / VENTANA MODAL PARA CREAR ZONA
  # ------------------------------------------------------------------
  def _abrir_formulario_zona(self):
    ventana_zona = tk.Toplevel(self.root)
    ventana_zona.title("Crear Nueva Zona")
    ventana_zona.geometry("320x350")
    ventana_zona.resizable(False, False)
    ventana_zona.grab_set()

    ttk.Label(ventana_zona, text="Nombre de la Zona:").pack(
        anchor="w", padx=20, pady=(15, 2)
    )
    entry_nombre = ttk.Entry(ventana_zona)
    entry_nombre.pack(fill="x", padx=20)

    frame_x = ttk.Frame(ventana_zona)
    frame_x.pack(fill="x", padx=20, pady=5)
    ttk.Label(frame_x, text="X Mín (0-1000):").grid(row=0, column=0, sticky="w")
    entry_x_min = ttk.Entry(frame_x, width=10)
    entry_x_min.grid(row=0, column=1, padx=5)

    ttk.Label(frame_x, text="X Máx (0-1000):").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_x_max = ttk.Entry(frame_x, width=10)
    entry_x_max.grid(row=1, column=1, padx=5, pady=5)

    frame_y = ttk.Frame(ventana_zona)
    frame_y.pack(fill="x", padx=20, pady=5)
    ttk.Label(frame_y, text="Y Mín (0-1000):").grid(row=0, column=0, sticky="w")
    entry_y_min = ttk.Entry(frame_y, width=10)
    entry_y_min.grid(row=0, column=1, padx=5)

    ttk.Label(frame_y, text="Y Máx (0-1000):").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_y_max = ttk.Entry(frame_y, width=10)
    entry_y_max.grid(row=1, column=1, padx=5, pady=5)

    var_poblada = tk.BooleanVar(value=False)
    check_poblada = ttk.Checkbutton(
        ventana_zona, text="¿Es Zona Poblada?", variable=var_poblada
    )
    check_poblada.pack(anchor="w", padx=20, pady=10)

    def guardar_zona():
      nombre = entry_nombre.get().strip()

      if not nombre:
        messagebox.showerror(
            "Error de Validación",
            "El nombre de la zona no puede estar vacío.",
            parent=ventana_zona,
        )
        return

      for z in self.escenario.zonas:
        if z.nombre.lower() == nombre.lower():
          messagebox.showerror(
              "Error de Validación",
              f"Ya existe una zona con el nombre '{nombre}'.",
              parent=ventana_zona,
          )
          return

      try:
        x_min = float(entry_x_min.get())
        x_max = float(entry_x_max.get())
        y_min = float(entry_y_min.get())
        y_max = float(entry_y_max.get())
      except ValueError:
        messagebox.showerror(
            "Error de Validación",
            "Las coordenadas deben ser números válidos.",
            parent=ventana_zona,
        )
        return

      if not (0 <= x_min <= 1000 and 0 <= x_max <= 1000):
        messagebox.showerror(
            "Error de Rangos",
            "Las coordenadas X deben estar entre 0 y 1000 km.",
            parent=ventana_zona,
        )
        return

      if not (0 <= y_min <= 1000 and 0 <= y_max <= 1000):
        messagebox.showerror(
            "Error de Rangos",
            "Las coordenadas Y deben estar entre 0 y 1000 km.",
            parent=ventana_zona,
        )
        return

      if x_min >= x_max or y_min >= y_max:
        messagebox.showerror(
            "Error de Geometría",
            "Los valores mínimos deben ser menores que los máximos.",
            parent=ventana_zona,
        )
        return

      nueva_zona = Zona(
          nombre=nombre,
          x_min=x_min,
          x_max=x_max,
          y_min=y_min,
          y_max=y_max,
          poblada=var_poblada.get(),
      )
      self.escenario.zonas.append(nueva_zona)

      messagebox.showinfo(
          "Éxito",
          f"Zona '{nombre}' guardada con éxito en el escenario.",
          parent=ventana_zona,
      )
      ventana_zona.destroy()

    btn_guardar = ttk.Button(
        ventana_zona, text="Guardar Zona", command=guardar_zona
    )
    btn_guardar.pack(pady=15)

  # ------------------------------------------------------------------
  # FORMULARIO / VENTANA MODAL PARA CREAR ESTACIÓN
  # ------------------------------------------------------------------
  def _abrir_formulario_estacion(self):
    if not self.escenario.zonas:
      messagebox.showwarning(
          "Atención",
          "No hay zonas registradas en el escenario.\nDebes crear al menos"
          " una zona primero.",
      )
      return

    ventana_est = tk.Toplevel(self.root)
    ventana_est.title("Crear Nueva Estación")
    ventana_est.geometry("340x360")
    ventana_est.resizable(False, False)
    ventana_est.grab_set()

    frame_info = ttk.Frame(ventana_est)
    frame_info.pack(fill="x", padx=20, pady=(15, 5))

    ttk.Label(frame_info, text="ID Estación:").grid(
        row=0, column=0, sticky="w", pady=5
    )
    entry_id = ttk.Entry(frame_info, width=18)
    entry_id.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_info, text="Nombre:").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_nombre = ttk.Entry(frame_info, width=18)
    entry_nombre.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(frame_info, text="Zona:").grid(
        row=2, column=0, sticky="w", pady=5
    )
    zonas_dict = {z.nombre: z for z in self.escenario.zonas}
    combo_zona = ttk.Combobox(
        frame_info,
        values=list(zonas_dict.keys()),
        state="readonly",
        width=16,
    )
    combo_zona.grid(row=2, column=1, padx=5, pady=5)
    combo_zona.current(0)

    frame_coords = ttk.Frame(ventana_est)
    frame_coords.pack(fill="x", padx=20, pady=5)

    ttk.Label(frame_coords, text="Coordenada X (0-1000):").grid(
        row=0, column=0, sticky="w", pady=5
    )
    entry_x = ttk.Entry(frame_coords, width=10)
    entry_x.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_coords, text="Coordenada Y (0-1000):").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_y = ttk.Entry(frame_coords, width=10)
    entry_y.grid(row=1, column=1, padx=5, pady=5)

    def guardar_estacion():
      id_estacion = entry_id.get().strip()
      nombre = entry_nombre.get().strip()
      nombre_zona = combo_zona.get()

      if not id_estacion or not nombre:
        messagebox.showerror(
            "Error de Validación",
            "El ID y el Nombre de la estación son obligatorios.",
            parent=ventana_est,
        )
        return

      for e in self.escenario.estaciones:
        if e.id_estacion.lower() == id_estacion.lower():
          messagebox.showerror(
              "Error de Validación",
              f"Ya existe una estación con el ID '{id_estacion}'.",
              parent=ventana_est,
          )
          return

      try:
        x = float(entry_x.get())
        y = float(entry_y.get())
      except ValueError:
        messagebox.showerror(
            "Error de Validación",
            "Las coordenadas X e Y deben ser números válidos.",
            parent=ventana_est,
        )
        return

      if not (0 <= x <= 1000 and 0 <= y <= 1000):
        messagebox.showerror(
            "Error de Rangos",
            "Las coordenadas (X, Y) deben estar entre 0 y 1000 km.",
            parent=ventana_est,
        )
        return

      zona_seleccionada = zonas_dict[nombre_zona]

      try:
        nueva_estacion = Estacion(
            id_estacion=id_estacion,
            nombre=nombre,
            x=x,
            y=y,
            zona=zona_seleccionada,
        )
      except ValueError as err:
        messagebox.showerror("Error de Ubicación", str(err), parent=ventana_est)
        return

      self.escenario.estaciones.append(nueva_estacion)

      tipo_zona = "Poblada" if nueva_estacion.es_poblada else "No Poblada"
      messagebox.showinfo(
          "Éxito",
          f"Estación '{nombre}' (ID: {id_estacion}) registrada con éxito.\n"
          f"Asignada a la zona: '{zona_seleccionada.nombre}' ({tipo_zona}).",
          parent=ventana_est,
      )
      ventana_est.destroy()

    btn_guardar = ttk.Button(
        ventana_est, text="Verificar y Guardar", command=guardar_estacion
    )
    btn_guardar.pack(pady=15)

  # ------------------------------------------------------------------
  # FORMULARIO / VENTANA MODAL PARA CREAR EPICENTRO
  # ------------------------------------------------------------------
  def _abrir_formulario_epicentro(self):
    if not self.escenario.zonas:
      messagebox.showwarning(
          "Atención",
          "No hay zonas registradas en el escenario.\nDebes crear al menos"
          " una zona primero.",
      )
      return

    ventana_epi = tk.Toplevel(self.root)
    ventana_epi.title("Crear Nuevo Epicentro")
    ventana_epi.geometry("300x220")
    ventana_epi.resizable(False, False)
    ventana_epi.grab_set()

    frame_coords = ttk.Frame(ventana_epi)
    frame_coords.pack(fill="x", padx=20, pady=20)

    ttk.Label(frame_coords, text="Coordenada X (0-1000):").grid(
        row=0, column=0, sticky="w", pady=5
    )
    entry_x = ttk.Entry(frame_coords, width=10)
    entry_x.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(frame_coords, text="Coordenada Y (0-1000):").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_y = ttk.Entry(frame_coords, width=10)
    entry_y.grid(row=1, column=1, padx=5, pady=5)

    def guardar_epicentro():
      try:
        x = float(entry_x.get())
        y = float(entry_y.get())
      except ValueError:
        messagebox.showerror(
            "Error de Validación",
            "Las coordenadas deben ser números válidos.",
            parent=ventana_epi,
        )
        return

      if not (0 <= x <= 1000 and 0 <= y <= 1000):
        messagebox.showerror(
            "Error de Rangos",
            "Las coordenadas (X, Y) deben estar entre 0 y 1000 km.",
            parent=ventana_epi,
        )
        return

      nuevo_epicentro = Epicentro(
          x=x, y=y, zonas_escenario=self.escenario.zonas
      )

      if nuevo_epicentro.zona is None:
        messagebox.showerror(
            "Error de Pertenece a Zona",
            f"El punto ({nuevo_epicentro.x}, {nuevo_epicentro.y}) no pertenece"
            " a ninguna zona registrada en el escenario.",
            parent=ventana_epi,
        )
        return

      self.escenario.epicentros.append(nuevo_epicentro)

      tipo_zona = "Poblada" if nuevo_epicentro.es_poblada else "No Poblada"
      messagebox.showinfo(
          "Éxito",
          f"Epicentro en ({nuevo_epicentro.x}, {nuevo_epicentro.y}) verificado"
          " correctamente.\nPertenece a la zona:"
          f" '{nuevo_epicentro.zona.nombre}' ({tipo_zona})",
          parent=ventana_epi,
      )
      ventana_epi.destroy()

    btn_guardar = ttk.Button(
        ventana_epi, text="Verificar y Crear", command=guardar_epicentro
    )
    btn_guardar.pack(pady=10)

  # ------------------------------------------------------------------
  # FORMULARIO / VENTANA MODAL PARA CREAR EVENTO
  # ------------------------------------------------------------------
  def _abrir_formulario_evento(self):
    if not self.escenario.epicentros:
      messagebox.showwarning(
          "Atención",
          "No hay epicentros registrados.\nDebes crear al menos un epicentro"
          " antes de registrar un evento.",
      )
      return

    if not self.escenario.estaciones:
      messagebox.showwarning(
          "Atención",
          "No hay estaciones registradas.\nDebes crear al menos una estación"
          " de origen antes de registrar un evento.",
      )
      return

    ventana_evt = tk.Toplevel(self.root)
    ventana_evt.title("Crear Nuevo Evento Sísmico")
    ventana_evt.geometry("380x380")
    ventana_evt.resizable(False, False)
    ventana_evt.grab_set()

    frame_campos = ttk.Frame(ventana_evt)
    frame_campos.pack(fill="x", padx=20, pady=15)

    # ID Evento
    ttk.Label(frame_campos, text="ID Evento (1 - 999999):").grid(
        row=0, column=0, sticky="w", pady=5
    )
    entry_id = ttk.Entry(frame_campos, width=18)
    entry_id.grid(row=0, column=1, padx=5, pady=5)

    # Magnitud
    ttk.Label(frame_campos, text="Magnitud (-2.0 a 10.0):").grid(
        row=1, column=0, sticky="w", pady=5
    )
    entry_mag = ttk.Entry(frame_campos, width=18)
    entry_mag.grid(row=1, column=1, padx=5, pady=5)

    # Profundidad
    ttk.Label(frame_campos, text="Profundidad (0 - 700 km):").grid(
        row=2, column=0, sticky="w", pady=5
    )
    entry_prof = ttk.Entry(frame_campos, width=18)
    entry_prof.grid(row=2, column=1, padx=5, pady=5)

    # Selector de Epicentro
    ttk.Label(frame_campos, text="Epicentro:").grid(
        row=3, column=0, sticky="w", pady=5
    )
    epicentros_dict = {
        f"({epi.x}, {epi.y}) - {epi.zona.nombre if epi.zona else 'Sin Zona'}": (
            epi
        )
        for epi in self.escenario.epicentros
    }
    combo_epicentro = ttk.Combobox(
        frame_campos,
        values=list(epicentros_dict.keys()),
        state="readonly",
        width=22,
    )
    combo_epicentro.grid(row=3, column=1, padx=5, pady=5)
    combo_epicentro.current(0)

    # Selector de Estación Origen
    ttk.Label(frame_campos, text="Estación Origen:").grid(
        row=4, column=0, sticky="w", pady=5
    )
    estaciones_dict = {
        f"{est.id_estacion} - {est.nombre}": est
        for est in self.escenario.estaciones
    }
    combo_estacion = ttk.Combobox(
        frame_campos,
        values=list(estaciones_dict.keys()),
        state="readonly",
        width=22,
    )
    combo_estacion.grid(row=4, column=1, padx=5, pady=5)
    combo_estacion.current(0)

    # Fecha/Hora Opcional
    ttk.Label(
        frame_campos, text="Fecha/Hora (ISO):", font=("Arial", 9, "italic")
    ).grid(row=5, column=0, sticky="w", pady=5)
    entry_fecha = ttk.Entry(frame_campos, width=18)
    entry_fecha.grid(row=5, column=1, padx=5, pady=5)

    def guardar_evento():
      try:
        id_evento = int(entry_id.get().strip())
        if not (1 <= id_evento <= 999999):
          raise ValueError()
      except ValueError:
        messagebox.showerror(
            "Error de Validación",
            "El ID del evento debe ser un número entero entre 1 y 999999.",
            parent=ventana_evt,
        )
        return

      try:
        magnitud = float(entry_mag.get().strip())
        profundidad = float(entry_prof.get().strip())
      except ValueError:
        messagebox.showerror(
            "Error de Validación",
            "La magnitud y la profundidad deben ser números válidos.",
            parent=ventana_evt,
        )
        return

      if not (-2.0 <= magnitud <= 10.0):
        messagebox.showerror(
            "Error de Rango",
            "La magnitud debe estar entre -2.0 y 10.0.",
            parent=ventana_evt,
        )
        return

      if not (0.0 <= profundidad <= 700.0):
        messagebox.showerror(
            "Error de Rango",
            "La profundidad debe estar entre 0.0 y 700.0 km.",
            parent=ventana_evt,
        )
        return

      epicentro_sel = epicentros_dict[combo_epicentro.get()]
      estacion_sel = estaciones_dict[combo_estacion.get()]
      fecha_txt = entry_fecha.get().strip() or None

      # Instanciar Evento y Encapsularlo en un Nodo
      nuevo_evento = Evento(
          id_evento=id_evento,
          magnitud=magnitud,
          profundidad=profundidad,
          epicentro=epicentro_sel,
          estacion_origen=estacion_sel,
          fecha_hora=fecha_txt,
      )
      nuevo_nodo = Nodo(evento=nuevo_evento)

      # Insertar el nodo en el árbol AVL del escenario
      if getattr(self.escenario, "arbol_avl", None) is not None:
        self.escenario.arbol_avl.insertar(nuevo_nodo)

      messagebox.showinfo(
          "Éxito",
          f"Evento SIS-{nuevo_evento.id:06d} registrado e insertado en el"
          " árbol AVL.\n\n"
          f"• Prioridad: {nuevo_evento.prioridad}\n"
          f"• Clave (P, M, ID): {nuevo_evento.clave}\n"
          f"• Estación origen: {estacion_sel.id_estacion}",
          parent=ventana_evt,
      )
      ventana_evt.destroy()

    btn_guardar = ttk.Button(
        ventana_evt, text="Guardar Evento", command=guardar_evento
    )
    btn_guardar.pack(pady=15)