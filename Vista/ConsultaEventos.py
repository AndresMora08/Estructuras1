from typing import Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk


class ConsultaEventos:

  def __init__(self, root: tk.Tk, eventos: Dict, arbol_avl: Optional[object] = None):
    self.ventana = tk.Toplevel(root)
    self.ventana.title("SismoLab - Consulta de Eventos")
    self.ventana.geometry("500x500")
    self.ventana.resizable(False, False)
    self.ventana.grab_set()

    self.eventos = eventos
    self.arbol_avl = arbol_avl  # Recibido para futuras métricas del árbol

    # 1. Construir la barra de búsqueda superior
    self._crear_interfaz_busqueda()

    # 2. Construir el panel donde se renderizan los datos encontrados
    self._crear_panel_resultados()

  def _crear_interfaz_busqueda(self):
    frame_busqueda = ttk.LabelFrame(self.ventana, text=" Buscar Evento por ID ")
    frame_busqueda.pack(fill="x", padx=15, pady=10)

    ttk.Label(frame_busqueda, text="ID Evento:").pack(
        side=tk.LEFT, padx=(10, 5), pady=10
    )

    self.entry_id = ttk.Entry(frame_busqueda, width=15)
    self.entry_id.pack(side=tk.LEFT, padx=5, pady=10)
    self.entry_id.focus()  # Pone el cursor directo en el campo

    # Botón que activa la validación y búsqueda
    btn_buscar = ttk.Button(
        frame_busqueda, text="Buscar", command=self._procesar_busqueda
    )
    btn_buscar.pack(side=tk.LEFT, padx=10, pady=10)

  def _crear_panel_resultados(self):
    # Panel contenedor de la información del evento
    self.frame_info = ttk.LabelFrame(
        self.ventana, text=" Detalles del Evento "
    )
    self.frame_info.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # Definición de etiquetas dinámicas
    self.lbl_id = ttk.Label(
        self.frame_info, text="ID: -", font=("Arial", 10, "bold")
    )
    self.lbl_id.pack(anchor="w", padx=15, pady=5)

    self.lbl_magnitud = ttk.Label(self.frame_info, text="Magnitud: -")
    self.lbl_magnitud.pack(anchor="w", padx=15, pady=2)

    self.lbl_profundidad = ttk.Label(self.frame_info, text="Profundidad: -")
    self.lbl_profundidad.pack(anchor="w", padx=15, pady=2)

    self.lbl_prioridad = ttk.Label(self.frame_info, text="Prioridad: -")
    self.lbl_prioridad.pack(anchor="w", padx=15, pady=2)

    self.lbl_clave = ttk.Label(self.frame_info, text="Clave AVL: -")
    self.lbl_clave.pack(anchor="w", padx=15, pady=2)

    # Nuevo dato: Zona Poblada
    self.lbl_poblada = ttk.Label(self.frame_info, text="¿Zona Poblada?: -")
    self.lbl_poblada.pack(anchor="w", padx=15, pady=2)

    self.lbl_estacion = ttk.Label(self.frame_info, text="Estación Origen: -")
    self.lbl_estacion.pack(anchor="w", padx=15, pady=2)

    self.lbl_fecha = ttk.Label(self.frame_info, text="Fecha/Hora: -")
    self.lbl_fecha.pack(anchor="w", padx=15, pady=2)

  def _procesar_busqueda(self):
    id_ingresado = self.entry_id.get().strip()

    if not id_ingresado:
      messagebox.showwarning(
          "Atención",
          "Por favor ingrese un ID para realizar la búsqueda.",
          parent=self.ventana,
      )
      return

    try:
      numero_id = int(id_ingresado)
      self._mostrar_evento(numero_id)
    except ValueError:
      messagebox.showerror(
          "Error de Validación",
          "Ingresa solo valores numéricos para consultar el evento por ID.",
          parent=self.ventana,
      )

  def _mostrar_evento(self, numero: int):
    if numero in self.eventos:
      evento_encontrado = self.eventos[numero]

      # Actualización de datos básicos
      self.lbl_id.config(text=f"ID Evento: SIS-{evento_encontrado.id:06d}")
      self.lbl_magnitud.config(
          text=f"Magnitud: {evento_encontrado.magnitud} Mw"
      )
      self.lbl_profundidad.config(
          text=f"Profundidad: {evento_encontrado.profundidad} km"
      )
      self.lbl_prioridad.config(text=f"Prioridad: {evento_encontrado.prioridad}")
      self.lbl_clave.config(text=f"Clave AVL (P, M, ID): {evento_encontrado.clave}")

      # Verificación segura de Pertenencia a Zona Poblada
      es_poblada = False
      if evento_encontrado.epicentro and evento_encontrado.epicentro.zona:
        es_poblada = evento_encontrado.epicentro.zona.poblada
      
      txt_poblada = "Sí" if es_poblada else "No"
      self.lbl_poblada.config(text=f"¿Zona Poblada?: {txt_poblada}")

      # Estación origen
      estacion_nom = (
          evento_encontrado.estacion_origen.nombre
          if evento_encontrado.estacion_origen
          else "N/A"
      )
      self.lbl_estacion.config(text=f"Estación Origen: {estacion_nom}")

      # Fecha u hora
      fecha_txt = (
          evento_encontrado.fecha_hora
          if getattr(evento_encontrado, "fecha_hora", None)
          else "No registrada"
      )
      self.lbl_fecha.config(text=f"Fecha/Hora: {fecha_txt}")

    else:
      self._limpiar_pantalla()
      messagebox.showwarning(
          "No Encontrado",
          f"El ID '{numero}' no pertenece a ningún evento en el sistema.",
          parent=self.ventana,
      )

  def _limpiar_pantalla(self):
    self.lbl_id.config(text="ID: -")
    self.lbl_magnitud.config(text="Magnitud: -")
    self.lbl_profundidad.config(text="Profundidad: -")
    self.lbl_prioridad.config(text="Prioridad: -")
    self.lbl_clave.config(text="Clave AVL: -")
    self.lbl_poblada.config(text="¿Zona Poblada?: -")
    self.lbl_estacion.config(text="Estación Origen: -")
    self.lbl_fecha.config(text="Fecha/Hora: -")