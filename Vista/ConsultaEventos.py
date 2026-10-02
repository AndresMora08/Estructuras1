from typing import Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk

from Vista.VentanaCorreccionManual import VentanaCorreccionManual
from Vista.VentanaEliminacionManual import VentanaEliminacionManual
from Vista.VentanaConsultaAvanzado import VentanaConsultaAvanzado


class ConsultaEventos:

    def __init__(
        self,
        root: tk.Tk,
        eventos: Dict,
        arbol_avl: Optional[object] = None,
        escenario: Optional[object] = None,
    ):
        self.ventana = tk.Toplevel(root)
        self.ventana.title("Consulta de Eventos")
        self.ventana.geometry("520x560")

        self.eventos = eventos
        self.arbol_avl = arbol_avl
        self.escenario = escenario
        self.evento_actual = None

        # Contenedor para búsqueda
        f_busqueda = ttk.Frame(self.ventana)
        f_busqueda.pack(pady=10)

        ttk.Label(f_busqueda, text="ID Evento:").pack(side=tk.LEFT, padx=5)
        self.entry_id = ttk.Entry(f_busqueda, width=10)
        self.entry_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(
            f_busqueda, text="Buscar", command=self._procesar_busqueda
        ).pack(side=tk.LEFT, padx=5)

        # Panel de detalles
        self.panel_info = ttk.LabelFrame(self.ventana, text=" Detalles ")
        self.panel_info.pack(fill="both", expand=True, padx=10, pady=10)

        # Diccionario dinámico para almacenar las etiquetas de texto
        self.labels = {}
        campos = [
            "ID",
            "Estado",
            "Revisión",
            "Magnitud",
            "Profundidad",
            "Prioridad",
            "Clave AVL",
            "Acceso Costoso",
        ]

        for campo in campos:
            lbl = ttk.Label(self.panel_info, text=f"{campo}: -")
            lbl.pack(anchor="w", padx=10, pady=2)
            self.labels[campo] = lbl

        # Botones de Acción
        f_botones = ttk.Frame(self.panel_info)
        f_botones.pack(pady=15)

        self.btn_corregir = ttk.Button(
            f_botones,
            text="Corregir",
            state="disabled",
            command=self._abrir_formulario_correccion,
        )
        self.btn_corregir.pack(side=tk.LEFT, padx=5)

        self.btn_estado = ttk.Button(
            f_botones,
            text="Marcar Revisado",
            state="disabled",
            command=self._alternar_estado_atencion,
        )
        self.btn_estado.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar = ttk.Button(
            f_botones,
            text="Eliminar",
            state="disabled",
            command=self._abrir_ventana_eliminacion,
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=5)

        self.btn_archivar = ttk.Button(
            f_botones,
            text="Archivar Rama Antigua",
            command=self._procesar_archivado_rama,
        )
        self.btn_archivar.pack(side=tk.LEFT, padx=5)

        # Botón para Consultas Avanzadas y Análisis de Desempeño
        f_avanzado = ttk.Frame(self.ventana)
        f_avanzado.pack(pady=10)

        self.btn_avanzado = ttk.Button(
            f_avanzado,
            text="Consultas Avanzadas y Análisis de Desempeño",
            command=self._abrir_consultas_avanzadas,
        )
        self.btn_avanzado.pack()

    def _abrir_consultas_avanzadas(self):
        VentanaConsultaAvanzado(
            parent_window=self.ventana,
            arbol_avl=self.arbol_avl,
            escenario=self.escenario,
            dict_eventos=self.eventos,
        )

    def _procesar_busqueda(self):
        try:
            num_id = int(self.entry_id.get().strip())
            self._mostrar_evento(num_id)
        except ValueError:
            messagebox.showerror(
                "Error", "Ingrese un ID numérico.", parent=self.ventana
            )

    def _mostrar_evento(self, num_id: int):
        if num_id in self.eventos:
            self.evento_actual = self.eventos[num_id]
            ev = self.evento_actual

            datos = {
                "ID": f"SIS-{ev.id:06d}",
                "Estado": ev.estado,
                "Revisión": f"r{ev.revision}",
                "Magnitud": f"{ev.magnitud} Mw",
                "Profundidad": f"{ev.profundidad} km",
                "Prioridad": ev.prioridad,
                "Clave AVL": str(ev.clave),
                "Acceso Costoso": (
                    "SÍ (Afectado por L)" if getattr(ev, "acceso_costoso", False) else "NO"
                ),
            }

            for clave, valor in datos.items():
                if clave in self.labels:
                    self.labels[clave].config(text=f"{clave}: {valor}")

            self.btn_corregir.config(state="normal")
            self.btn_estado.config(state="normal")
            self.btn_eliminar.config(state="normal")
            self.btn_estado.config(
                text=(
                    "Marcar Pendiente"
                    if ev.estado == "Revisado"
                    else "Marcar Revisado"
                )
            )
        else:
            self._limpiar_pantalla()
            messagebox.showwarning(
                "Aviso", f"El ID {num_id} no existe.", parent=self.ventana
            )

    def _alternar_estado_atencion(self):
        if self.evento_actual:
            nuevo_estado = (
                "Pendiente"
                if self.evento_actual.estado == "Revisado"
                else "Revisado"
            )
            self.evento_actual.estado = nuevo_estado
            self._mostrar_evento(self.evento_actual.id)

    def _abrir_formulario_correccion(self):
        if self.evento_actual:
            VentanaCorreccionManual(
                parent_window=self.ventana,
                evento_viejo=self.evento_actual,
                arbol_avl=self.arbol_avl,
                dict_eventos=self.eventos,
                escenario=self.escenario,
                callback_refrescar=lambda: self._mostrar_evento(
                    self.evento_actual.id
                ),
            )

    def _abrir_ventana_eliminacion(self):
        if self.evento_actual:
            VentanaEliminacionManual(
                parent_window=self.ventana,
                evento=self.evento_actual,
                arbol_avl=self.arbol_avl,
                dict_eventos=self.eventos,
                escenario=self.escenario,
                callback_al_eliminar=self._limpiar_pantalla,
            )

    def _procesar_archivado_rama(self):
        if not self.escenario:
            messagebox.showerror(
                "Error", "No hay un escenario activo cargado.", parent=self.ventana
            )
            return

        if not self.evento_actual:
            messagebox.showwarning(
                "Aviso",
                "Por favor, busque primero el evento que será la raíz de la rama a archivar.",
                parent=self.ventana,
            )
            return

        id_objetivo = self.evento_actual.id

        exito, justificacion, ids_afectados = self.escenario.archivar_evento_por_id(id_objetivo)

        if not exito:
            messagebox.showinfo("Información / No Elegible", justificacion, parent=self.ventana)
            return

        confirmar = messagebox.askyesno(
            "Confirmación de Archivado de Rama",
            f"{justificacion}\n\n¿Desea confirmar el archivado de este subárbol al histórico?",
            parent=self.ventana,
        )

        if not confirmar:
            self.escenario.deshacer_ultimo_archivado()
            messagebox.showinfo(
                "Cancelado",
                "Operación cancelada. El árbol conservó su estado original.",
                parent=self.ventana,
            )
        else:
            self._limpiar_pantalla()
            messagebox.showinfo(
                "Éxito",
                f"Se archivaron correctamente {len(ids_afectados)} eventos y se trasladaron al histórico.",
                parent=self.ventana,
            )

    def _limpiar_pantalla(self):
        self.evento_actual = None
        self.entry_id.delete(0, tk.END)
        for campo, lbl in self.labels.items():
            lbl.config(text=f"{campo}: -")
        self.btn_corregir.config(state="disabled")
        self.btn_estado.config(state="disabled", text="Marcar Revisado")
        self.btn_eliminar.config(state="disabled")