from typing import Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk

from Vista.VentanaCorreccionManual import VentanaCorreccionManual


class ConsultaEventos:

  def __init__(
      self, root: tk.Tk, eventos: Dict, arbol_avl: Optional[object] = None
  ):
    self.ventana = tk.Toplevel(root)
    self.ventana.title("SismoLab - Consulta de Eventos")
    self.ventana.geometry("500x560")
    self.ventana.resizable(False, False)
    self.ventana.grab_set()

    self.eventos = eventos
    self.arbol_avl = arbol_avl
    self.evento_actual = None  # Almacenará el evento encontrado

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
    self.entry_id.focus()

    btn_buscar = ttk.Button(
        frame_busqueda, text="Buscar", command=self._procesar_busqueda
    )
    btn_buscar.pack(side=tk.LEFT, padx=10, pady=10)

  def _crear_panel_resultados(self):
    self.frame_info = ttk.LabelFrame(
        self.ventana, text=" Detalles del Evento "
    )
    self.frame_info.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    self.lbl_id = ttk.Label(
        self.frame_info, text="ID: -", font=("Arial", 10, "bold")
    )
    self.lbl_id.pack(anchor="w", padx=15, pady=5)

    self.lbl_revision = ttk.Label(self.frame_info, text="Revisión: -")
    self.lbl_revision.pack(anchor="w", padx=15, pady=2)

    self.lbl_magnitud = ttk.Label(self.frame_info, text="Magnitud: -")
    self.lbl_magnitud.pack(anchor="w", padx=15, pady=2)

    self.lbl_profundidad = ttk.Label(self.frame_info, text="Profundidad: -")
    self.lbl_profundidad.pack(anchor="w", padx=15, pady=2)

    self.lbl_prioridad = ttk.Label(self.frame_info, text="Prioridad: -")
    self.lbl_prioridad.pack(anchor="w", padx=15, pady=2)

    self.lbl_clave = ttk.Label(self.frame_info, text="Clave AVL: -")
    self.lbl_clave.pack(anchor="w", padx=15, pady=2)

    self.lbl_poblada = ttk.Label(self.frame_info, text="¿Zona Poblada?: -")
    self.lbl_poblada.pack(anchor="w", padx=15, pady=2)

    self.lbl_estacion = ttk.Label(self.frame_info, text="Estación Origen: -")
    self.lbl_estacion.pack(anchor="w", padx=15, pady=2)

    self.lbl_fecha = ttk.Label(self.frame_info, text="Fecha/Hora: -")
    self.lbl_fecha.pack(anchor="w", padx=15, pady=2)

    # Frame para agrupar los botones de acción
    frame_botones = ttk.Frame(self.frame_info)
    frame_botones.pack(pady=12)

    # BOTÓN DE CORRECCIÓN
    self.btn_corregir = ttk.Button(
        frame_botones,
        text="Corregir Evento",
        state="disabled",
        command=self._abrir_formulario_correccion,
    )
    self.btn_corregir.pack(side=tk.LEFT, padx=5)

    # BOTÓN CAMBIAR ESTADO DE ATENCIÓN (Revisado / Pendiente)
    self.btn_estado = ttk.Button(
        frame_botones,
        text="Marcar como Revisado",
        state="disabled",
        command=self._alternar_estado_atencion,
    )
    self.btn_estado.pack(side=tk.LEFT, padx=5)

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
      self.evento_actual = self.eventos[numero]

      # Carga de datos
      self.lbl_id.config(
          text=(
              f"ID Evento: SIS-{self.evento_actual.id:06d} | Estado:"
              f" {self.evento_actual.estado}"
          )
      )
      self.lbl_revision.config(
          text=f"Revisión Vigente: r{self.evento_actual.revision}"
      )
      self.lbl_magnitud.config(text=f"Magnitud: {self.evento_actual.magnitud} Mw")
      self.lbl_profundidad.config(
          text=f"Profundidad: {self.evento_actual.profundidad} km"
      )
      self.lbl_prioridad.config(text=f"Prioridad: {self.evento_actual.prioridad}")
      self.lbl_clave.config(
          text=f"Clave AVL (P, M, ID): {self.evento_actual.clave}"
      )

      es_poblada = False
      if self.evento_actual.epicentro and self.evento_actual.epicentro.zona:
        es_poblada = self.evento_actual.epicentro.zona.poblada

      self.lbl_poblada.config(text=f"¿Zona Poblada?: {'Sí' if es_poblada else 'No'}")

      estacion_nom = (
          self.evento_actual.estacion_origen.nombre
          if self.evento_actual.estacion_origen
          else "N/A"
      )
      self.lbl_estacion.config(text=f"Estación Origen: {estacion_nom}")

      fecha_txt = (
          self.evento_actual.fecha_hora
          if getattr(self.evento_actual, "fecha_hora", None)
          else "No registrada"
      )
      self.lbl_fecha.config(text=f"Fecha/Hora: {fecha_txt}")

      # Habilitar los botones de acción
      self.btn_corregir.config(state="normal")
      self.btn_estado.config(state="normal")

      # Adaptar el texto del botón de estado según el estado actual
      if self.evento_actual.estado == "Revisado":
        self.btn_estado.config(text="Deshacer: Marcar Pendiente")
      else:
        self.btn_estado.config(text="Marcar como Revisado")

    else:
      self._limpiar_pantalla()
      messagebox.showwarning(
          "No Encontrado",
          f"El ID '{numero}' no pertenece a ningún evento en el sistema.",
          parent=self.ventana,
      )

  def _alternar_estado_atencion(self):
    """Cambia el estado de atención de 'Pendiente' a 'Revisado' o viceversa."""
    if not self.evento_actual:
      return

    if self.evento_actual.estado == "Revisado":
      self.evento_actual.estado = "Pendiente"
      msg = "El evento ha sido marcado nuevamente como PENDIENTE."
    else:
      self.evento_actual.estado = "Revisado"
      msg = "El evento ha sido marcado como REVISADO."

    # Refrescar los detalles mostrados en pantalla
    self._mostrar_evento(self.evento_actual.id)
    messagebox.showinfo("Estado Actualizado", msg, parent=self.ventana)

  def _abrir_formulario_correccion(self):
    if self.evento_actual:
      VentanaCorreccionManual(
          parent_window=self.ventana,
          evento_viejo=self.evento_actual,
          arbol_avl=self.arbol_avl,
          dict_eventos=self.eventos,
          callback_refrescar=lambda: self._mostrar_evento(
              self.evento_actual.id
          ),
      )

  def _limpiar_pantalla(self):
    self.evento_actual = None
    self.lbl_id.config(text="ID: -")
    self.lbl_revision.config(text="Revisión: -")
    self.lbl_magnitud.config(text="Magnitud: -")
    self.lbl_profundidad.config(text="Profundidad: -")
    self.lbl_prioridad.config(text="Prioridad: -")
    self.lbl_clave.config(text="Clave AVL: -")
    self.lbl_poblada.config(text="¿Zona Poblada?: -")
    self.lbl_estacion.config(text="Estación Origen: -")
    self.lbl_fecha.config(text="Fecha/Hora: -")
    self.btn_corregir.config(state="disabled")
    self.btn_estado.config(state="disabled", text="Marcar como Revisado")