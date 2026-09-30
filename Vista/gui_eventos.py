import tkinter as tk
from tkinter import messagebox, ttk

from Vista.ConsultaEventos import ConsultaEventos
from Vista.VentanaEliminacionManual import VentanaEliminacionManual
from Vista.VisualizadorAVL import VisualizadorAVL


class EventosMixin:

    # ==================================================================
    # CONSULTA DE EVENTOS
    # ==================================================================

    def _abrir_busqueda(self):

        dict_eventos = getattr(
            self.escenario,
            "dict_eventos",
            {}
        )

        if not dict_eventos:

            messagebox.showinfo(
                "Sin Eventos",
                "No hay registro de eventos en el sistema.",
                parent=self.root
            )

            return

        ConsultaEventos(
            self.root,
            dict_eventos,
            getattr(
                self.escenario,
                "arbol_avl",
                None
            ),
            self.escenario
        )

    # ==================================================================
    # VISUALIZADOR AVL
    # ==================================================================

    def _abrir_visualizador_arbol(self):

        arbol = getattr(
            self.escenario,
            "arbol_avl",
            None
        )

        if not arbol or not arbol.raiz:

            messagebox.showinfo(
                "Árbol Vacío",
                "El árbol AVL no contiene eventos registrados aún.",
                parent=self.root
            )

            return

        VisualizadorAVL(
            self.root,
            arbol
        )

    # ==================================================================
    # GESTIÓN Y JSON
    # ==================================================================

    def abrir_ventana_gestion(self):

        dict_eventos = getattr(
            self.escenario,
            "dict_eventos",
            {}
        )

        if not dict_eventos:

            messagebox.showwarning(
                "Advertencia",
                "No hay ningún evento disponible para gestionar o eliminar.",
                parent=self.root
            )

            return

        evento_actual = getattr(
            self,
            "evento_seleccionado",
            None
        )

        if not evento_actual:

            evento_actual = next(
                iter(dict_eventos.values()),
                None
            )

        if not evento_actual:

            messagebox.showwarning(
                "Advertencia",
                "No hay ningún evento disponible.",
                parent=self.root
            )

            return

        VentanaEliminacionManual(
            parent_window=self.root,
            evento=evento_actual,
            arbol_avl=getattr(
                self.escenario,
                "arbol_avl",
                None
            ),
            dict_eventos=dict_eventos,
            escenario=self.escenario,
            callback_al_eliminar=self.actualizar_interfaz
        )

    # ==================================================================
    # TABLA DE EVENTOS
    #
    # Este método se conserva, pero ya no se ejecuta al iniciar
    # la ventana principal.
    # ==================================================================

    def configurar_tabla_eventos(
        self,
        parent_frame
    ):

        columnas = (
            "ID",
            "Fecha / Hora",
            "Magnitud",
            "Profundidad",
            "Epicentro X",
            "Epicentro Y",
            "Estado",
            "Ref. / Principal"
        )

        self.tabla_eventos = ttk.Treeview(
            parent_frame,
            columns=columnas,
            show="headings"
        )

        anchos = [
            60,
            180,
            80,
            90,
            100,
            100,
            100,
            160
        ]

        for col, ancho in zip(
            columnas,
            anchos
        ):

            self.tabla_eventos.heading(
                col,
                text=col
            )

            self.tabla_eventos.column(
                col,
                width=ancho,
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            parent_frame,
            orient="vertical",
            command=self.tabla_eventos.yview
        )

        self.tabla_eventos.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabla_eventos.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    # ==================================================================
    # ACTUALIZAR TABLA
    # ==================================================================

    def actualizar_tabla_eventos(self):

        if not hasattr(
            self,
            "tabla_eventos"
        ):
            return

        # --------------------------------------------------------------
        # LIMPIAR TABLA
        # --------------------------------------------------------------

        for item in self.tabla_eventos.get_children():

            self.tabla_eventos.delete(
                item
            )

        if not self.escenario:

            return

        # --------------------------------------------------------------
        # OBTENER EVENTOS
        # --------------------------------------------------------------

        eventos = []

        if (
            hasattr(
                self.escenario,
                "arbol_eventos"
            )
            and self.escenario.arbol_eventos
        ):

            try:

                if hasattr(
                    self.escenario.arbol_eventos,
                    "obtener_todos_los_eventos"
                ):

                    eventos = (
                        self.escenario
                        .arbol_eventos
                        .obtener_todos_los_eventos()
                    )

                elif hasattr(
                    self.escenario.arbol_eventos,
                    "inorden"
                ):

                    eventos = (
                        self.escenario
                        .arbol_eventos
                        .inorden()
                    )

                else:

                    eventos = list(
                        self.escenario.arbol_eventos
                    )

            except Exception:

                eventos = list(
                    getattr(
                        self.escenario,
                        "dict_eventos",
                        {}
                    ).values()
                )

        elif hasattr(
            self.escenario,
            "dict_eventos"
        ):

            eventos = list(
                self.escenario.dict_eventos.values()
            )

        elif hasattr(
            self.escenario,
            "eventos"
        ):

            eventos = self.escenario.eventos

        # --------------------------------------------------------------
        # INSERTAR EVENTOS
        # --------------------------------------------------------------

        for ev in eventos:

            # ----------------------------------------------------------
            # ID
            # ----------------------------------------------------------

            id_evento = getattr(
                ev,
                "id",
                getattr(
                    ev,
                    "id_evento",
                    ""
                )
            )

            # ----------------------------------------------------------
            # FECHA
            # ----------------------------------------------------------

            fecha = getattr(
                ev,
                "fecha_hora",
                getattr(
                    ev,
                    "fecha",
                    ""
                )
            )

            # ----------------------------------------------------------
            # MAGNITUD
            # ----------------------------------------------------------

            magnitud = getattr(
                ev,
                "magnitud",
                ""
            )

            # ----------------------------------------------------------
            # PROFUNDIDAD
            # ----------------------------------------------------------

            profundidad = getattr(
                ev,
                "profundidad",
                ""
            )

            # ----------------------------------------------------------
            # EPICENTRO
            # ----------------------------------------------------------

            epicentro = getattr(
                ev,
                "epicentro",
                None
            )

            if epicentro is not None:

                if hasattr(
                    epicentro,
                    "x"
                ):

                    x = epicentro.x

                elif isinstance(
                    epicentro,
                    (tuple, list)
                ):

                    x = epicentro[0]

                else:

                    x = ""

                if hasattr(
                    epicentro,
                    "y"
                ):

                    y = epicentro.y

                elif isinstance(
                    epicentro,
                    (tuple, list)
                ):

                    y = epicentro[1]

                else:

                    y = ""

            else:

                x = ""
                y = ""

            # ----------------------------------------------------------
            # ESTADO
            # ----------------------------------------------------------

            estado = getattr(
                ev,
                "estado",
                ""
            )

            if hasattr(
                estado,
                "value"
            ):

                estado = estado.value

            else:

                estado = str(
                    estado
                )

            # ----------------------------------------------------------
            # REFERENCIA
            # ----------------------------------------------------------

            id_referencia = getattr(
                ev,
                "id_referencia",
                None
            )

            if id_referencia is not None:

                ref_str = str(
                    id_referencia
                )

            else:

                ref_str = "Ninguna (Principal)"

            # ----------------------------------------------------------
            # INSERTAR
            # ----------------------------------------------------------

            self.tabla_eventos.insert(
                "",
                "end",
                values=(
                    id_evento,
                    fecha,
                    magnitud,
                    profundidad,
                    x,
                    y,
                    estado,
                    ref_str
                )
            )