from typing import Dict, Optional
import tkinter as tk
from tkinter import messagebox, ttk

from Modelos import Metricas
from Modelos.Asociaciones import (
    candidatos_de,
    estado_en_catalogo,
    replicas_de,
    seleccionar_referencia,
)
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
        self.ventana.geometry("640x700")

        # Fallback references; the live ones are read from the scenario
        self._eventos_inicial = eventos
        self._arbol_inicial = arbol_avl
        self.escenario = escenario
        self.evento_actual = None  # only set for ACTIVE events

        f_busqueda = ttk.Frame(self.ventana)
        f_busqueda.pack(pady=10)

        ttk.Label(f_busqueda, text="ID Evento:").pack(side=tk.LEFT, padx=5)
        self.entry_id = ttk.Entry(f_busqueda, width=10)
        self.entry_id.pack(side=tk.LEFT, padx=5)
        self.entry_id.bind("<Return>", lambda e: self._procesar_busqueda())
        ttk.Button(
            f_busqueda, text="Buscar", command=self._procesar_busqueda
        ).pack(side=tk.LEFT, padx=5)

        self.panel_info = ttk.LabelFrame(self.ventana, text=" Detalles ")
        self.panel_info.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_detalle = tk.Text(
            self.panel_info, wrap="word", font=("Consolas", 9), height=24, state="disabled"
        )
        sb = ttk.Scrollbar(self.panel_info, orient="vertical", command=self.txt_detalle.yview)
        self.txt_detalle.configure(yscrollcommand=sb.set)
        self.txt_detalle.pack(side=tk.LEFT, fill="both", expand=True, padx=(5, 0), pady=5)
        sb.pack(side=tk.RIGHT, fill="y", pady=5)

        f_botones = ttk.Frame(self.ventana)
        f_botones.pack(pady=8)

        self.btn_corregir = ttk.Button(
            f_botones, text="Corregir", state="disabled", command=self._abrir_formulario_correccion
        )
        self.btn_corregir.pack(side=tk.LEFT, padx=5)

        self.btn_estado = ttk.Button(
            f_botones, text="Marcar Revisado", state="disabled", command=self._alternar_estado_atencion
        )
        self.btn_estado.pack(side=tk.LEFT, padx=5)

        self.btn_eliminar = ttk.Button(
            f_botones, text="Eliminar", state="disabled", command=self._abrir_ventana_eliminacion
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=5)

        self.btn_archivar = ttk.Button(
            f_botones, text="Archivar Rama Antigua", command=self._procesar_archivado_rama
        )
        self.btn_archivar.pack(side=tk.LEFT, padx=5)

        f_avanzado = ttk.Frame(self.ventana)
        f_avanzado.pack(pady=8)
        ttk.Button(
            f_avanzado,
            text="Consultas Avanzadas y Análisis de Desempeño",
            command=self._abrir_consultas_avanzadas,
        ).pack()

    # ------------------------------------------------------------------
    # LIVE REFERENCES (undo / version restore replace these objects)
    # ------------------------------------------------------------------
    @property
    def eventos(self) -> Dict:
        if self.escenario is not None:
            return self.escenario.dict_eventos
        return self._eventos_inicial

    @property
    def arbol_avl(self):
        if self.escenario is not None:
            return self.escenario.arbol_avl
        return self._arbol_inicial

    def _abrir_consultas_avanzadas(self):
        VentanaConsultaAvanzado(
            parent_window=self.ventana,
            arbol_avl=self.arbol_avl,
            escenario=self.escenario,
            dict_eventos=self.eventos,
        )

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    def _procesar_busqueda(self):
        try:
            num_id = int(self.entry_id.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un ID numérico.", parent=self.ventana)
            return
        self._mostrar_evento(num_id)

    def _escribir(self, lineas):
        self.txt_detalle.config(state="normal")
        self.txt_detalle.delete("1.0", tk.END)
        self.txt_detalle.insert(tk.END, "\n".join(lineas))
        self.txt_detalle.config(state="disabled")

    def _etiqueta(self, id_evento: int) -> str:
        estado, _ = estado_en_catalogo(self.escenario, id_evento)
        return f"SIS-{id_evento:06d} [{estado or '?'}]"

    def _lista_ids(self, eventos) -> str:
        if not eventos:
            return "Ninguno"
        return ", ".join(self._etiqueta(e.id) for e in eventos)

    def _mostrar_evento(self, num_id: int):
        if self.escenario is None:
            messagebox.showerror("Error", "No hay un escenario activo.", parent=self.ventana)
            return

        estado, ev = estado_en_catalogo(self.escenario, num_id)
        if ev is None:
            self._limpiar_pantalla(conservar_id=True)
            messagebox.showwarning("Aviso", f"El ID {num_id} no existe.", parent=self.ventana)
            return

        esc = self.escenario
        epi = ev.epicentro
        zona = epi.zona if epi is not None else None
        texto_estado = {"Activo": "ACTIVO", "Archivado": "ARCHIVADO (en el histórico)",
                        "Retirado": "ELIMINADO (identificador retirado)"}.get(estado, str(estado))

        lineas = [
            f"Estado en catálogo : {texto_estado}",
            f"ID                 : SIS-{ev.id:06d}",
            f"Magnitud           : {ev.magnitud} Mw",
            f"Profundidad (hipo) : {ev.profundidad} km",
            f"Epicentro          : ({epi.x}, {epi.y})" if epi else "Epicentro          : -",
            f"Zona               : {zona.nombre if zona else 'Sin zona'}"
            f" ({'poblada' if zona and zona.poblada else 'no poblada'})",
            f"Fecha/hora (UTC)   : {ev.fecha_hora}",
            f"Revisión vigente   : r{ev.revision}",
            f"Estaciones         : {', '.join(ev.estaciones) if ev.estaciones else '-'}",
            f"Estado de atención : {ev.estado}",
            f"Prioridad          : {ev.prioridad}",
            f"Clave (P, M, I)    : {ev.clave}",
        ]

        if estado == "Activo":
            self.evento_actual = ev
            arbol = self.arbol_avl
            nodo, visitados = Metricas.costo_busqueda(arbol.raiz, ev.clave) if arbol else (None, 0)
            lineas.append("")
            lineas.append("--- Posición en el AVL ---")
            if nodo is not None:
                profundidad = visitados - 1
                alt_izq = nodo.izquierda.altura if nodo.izquierda is not None else -1
                alt_der = nodo.derecha.altura if nodo.derecha is not None else -1
                costoso = ev.prioridad == 3 and profundidad > esc.L
                lineas += [
                    f"Profundidad del nodo : {profundidad}",
                    f"Altura del nodo      : {nodo.altura}",
                    f"Factor de balance    : {alt_izq - alt_der}",
                    f"Nodos visitados al buscar su clave: {visitados}",
                    f"Acceso costoso       : {'SÍ' if costoso else 'NO'}"
                    f" (prioridad alta y profundidad > L={esc.L})",
                ]
            else:
                lineas.append("No se encontró el nodo por su clave (revise con 'Verificar estructura').")
        else:
            self.evento_actual = None
            lineas.append("")
            if estado == "Archivado":
                lineas.append("Fuera del AVL activo; conserva sus datos y asociaciones en el histórico.")
            else:
                lineas.append("Retirado del catálogo: su identificador no puede reutilizarse ni reactivarse")
                lineas.append("con reportes. Se recupera deshaciendo la eliminación o restaurando una versión.")

        if estado in ("Activo", "Archivado"):
            candidatos = candidatos_de(esc, ev)
            referencia = seleccionar_referencia(ev, candidatos)
            replicas = replicas_de(esc, ev.id)
            lineas += [
                "",
                f"--- Asociaciones (W={esc.W} h, R={esc.R} km) ---",
                f"Candidatos          : {self._lista_ids(candidatos)}",
                f"Referencia elegida  : {self._etiqueta(referencia) if referencia else 'Ninguna (sin asociación)'}",
                f"Réplicas que lo usan: {self._lista_ids(replicas)}",
            ]

        self._escribir(lineas)

        activo = estado == "Activo"
        self.btn_corregir.config(state="normal" if activo else "disabled")
        self.btn_estado.config(
            state="normal" if activo else "disabled",
            text="Marcar Pendiente" if (activo and ev.estado == "Revisado") else "Marcar Revisado",
        )
        self.btn_eliminar.config(state="normal" if activo else "disabled")

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def _alternar_estado_atencion(self):
        if not self.evento_actual:
            return

        # Always act on the LIVE event (undo may have replaced the objects)
        id_evento = self.evento_actual.id
        evento = self.eventos.get(id_evento)
        if evento is None:
            self._limpiar_pantalla()
            return

        if self.escenario is not None:
            self.escenario.guardar_estado_pila()

        evento.estado = "Pendiente" if evento.estado == "Revisado" else "Revisado"
        self._mostrar_evento(id_evento)

    def _abrir_formulario_correccion(self):
        if self.evento_actual:
            VentanaCorreccionManual(
                parent_window=self.ventana,
                evento_viejo=self.evento_actual,
                arbol_avl=self.arbol_avl,
                dict_eventos=self.eventos,
                escenario=self.escenario,
                callback_refrescar=lambda: self._mostrar_evento(self.evento_actual.id),
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
            messagebox.showerror("Error", "No hay un escenario activo cargado.", parent=self.ventana)
            return

        arbol = self.escenario.arbol_avl
        if arbol is None:
            messagebox.showerror(
                "Error", "El escenario no tiene un árbol AVL inicializado.", parent=self.ventana
            )
            return

        rama = arbol.buscar_rama_elegible_optima(self.escenario.reloj, self.escenario.T)

        if not rama:
            messagebox.showinfo(
                "Información",
                "No se encontró ninguna rama elegible para archivar.\n"
                "El estado del árbol se conserva.",
                parent=self.ventana,
            )
            return

        id_objetivo = rama["id_raiz"]
        cantidad_nodos = rama["cant_nodos"]
        profundidad = rama["profundidad"]
        ids_afectados = [f"SIS-{e.id:06d}" for e in rama["eventos"]]

        confirmar = messagebox.askyesno(
            "Confirmación de Archivado de Rama",
            (
                "Se encontró una rama elegible para archivar:\n\n"
                f"Raíz: SIS-{id_objetivo:06d}\n"
                f"Cantidad de nodos: {cantidad_nodos}\n"
                f"Profundidad de la raíz: {profundidad}\n"
                f"Identificadores afectados:\n{', '.join(ids_afectados)}\n\n"
                "Justificación: todos los eventos de la rama tienen prioridad baja "
                f"y antigüedad mayor que T = {self.escenario.T} h. Entre las ramas "
                "elegibles se eligió la de mayor cantidad de nodos "
                "(desempate: raíz más profunda, luego mayor identificador).\n\n"
                "¿Desea archivar esta rama en el histórico?"
            ),
            parent=self.ventana,
        )

        if not confirmar:
            messagebox.showinfo(
                "Cancelado",
                "Operación cancelada. El árbol conservó su estado original.",
                parent=self.ventana,
            )
            return

        exito, justificacion, ids = self.escenario.archivar_evento_por_id(id_objetivo)

        if not exito:
            messagebox.showinfo("Información / No Elegible", justificacion, parent=self.ventana)
            return

        self._limpiar_pantalla()
        messagebox.showinfo(
            "Éxito",
            f"Se archivaron correctamente {len(ids)} eventos y se trasladaron al histórico.",
            parent=self.ventana,
        )

    def _limpiar_pantalla(self, conservar_id: bool = False):
        self.evento_actual = None
        if not conservar_id:
            self.entry_id.delete(0, tk.END)
        self._escribir([])
        self.btn_corregir.config(state="disabled")
        self.btn_estado.config(state="disabled", text="Marcar Revisado")
        self.btn_eliminar.config(state="disabled")