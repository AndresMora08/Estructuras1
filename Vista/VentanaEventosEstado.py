import tkinter as tk
from tkinter import ttk


class VentanaEventosEstado:

    def __init__(self, parent, escenario):

        self.parent = parent
        self.escenario = escenario

        self.ventana = tk.Toplevel(parent)
        self.ventana.title("Eventos Activos e Histórico")
        self.ventana.geometry("1050x500")
        self.ventana.transient(parent)

        ttk.Label(
            self.ventana,
            text="Eventos del Sistema",
            font=("Arial", 14, "bold")
        ).pack(pady=10)

        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=10
        )

        self.tab_activos = ttk.Frame(self.notebook)
        self.tab_historico = ttk.Frame(self.notebook)

        self.notebook.add(
            self.tab_activos,
            text="Eventos Activos"
        )

        self.notebook.add(
            self.tab_historico,
            text="Histórico"
        )

        self._crear_tabla_activos()
        self._crear_tabla_historico()

        self.actualizar_tablas()

        f_botones = ttk.Frame(self.ventana)
        f_botones.pack(pady=(0, 10))

        ttk.Button(
            f_botones,
            text="Actualizar",
            command=self.actualizar_tablas
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            f_botones,
            text="Cerrar",
            command=self.ventana.destroy
        ).pack(side=tk.LEFT, padx=5)

    def _crear_tabla_activos(self):

        columnas = (
            "id",
            "fecha",
            "magnitud",
            "profundidad",
            "prioridad",
            "estado_atencion",
            "estado_catalogo"
        )

        self.tabla_activos = ttk.Treeview(
            self.tab_activos,
            columns=columnas,
            show="headings"
        )

        encabezados = {
            "id": "ID",
            "fecha": "Fecha-Hora",
            "magnitud": "Magnitud",
            "profundidad": "Profundidad",
            "prioridad": "Prioridad",
            "estado_atencion": "Atención",
            "estado_catalogo": "Catálogo"
        }

        anchos = {
            "id": 90,
            "fecha": 180,
            "magnitud": 90,
            "profundidad": 100,
            "prioridad": 80,
            "estado_atencion": 120,
            "estado_catalogo": 100
        }

        for columna in columnas:
            self.tabla_activos.heading(
                columna,
                text=encabezados[columna]
            )

            self.tabla_activos.column(
                columna,
                width=anchos[columna],
                anchor=tk.CENTER
            )

        scrollbar = ttk.Scrollbar(
            self.tab_activos,
            orient=tk.VERTICAL,
            command=self.tabla_activos.yview
        )

        self.tabla_activos.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabla_activos.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

    def _crear_tabla_historico(self):

        columnas = (
            "id",
            "fecha",
            "magnitud",
            "profundidad",
            "prioridad",
            "estado_atencion",
            "estado_catalogo"
        )

        self.tabla_historico = ttk.Treeview(
            self.tab_historico,
            columns=columnas,
            show="headings"
        )

        encabezados = {
            "id": "ID",
            "fecha": "Fecha-Hora",
            "magnitud": "Magnitud",
            "profundidad": "Profundidad",
            "prioridad": "Prioridad",
            "estado_atencion": "Atención",
            "estado_catalogo": "Catálogo"
        }

        anchos = {
            "id": 90,
            "fecha": 180,
            "magnitud": 90,
            "profundidad": 100,
            "prioridad": 80,
            "estado_atencion": 120,
            "estado_catalogo": 100
        }

        for columna in columnas:
            self.tabla_historico.heading(
                columna,
                text=encabezados[columna]
            )

            self.tabla_historico.column(
                columna,
                width=anchos[columna],
                anchor=tk.CENTER
            )

        scrollbar = ttk.Scrollbar(
            self.tab_historico,
            orient=tk.VERTICAL,
            command=self.tabla_historico.yview
        )

        self.tabla_historico.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabla_historico.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y
        )

    def actualizar_tablas(self):

        self._actualizar_tabla(
            self.tabla_activos,
            list(self.escenario.dict_eventos.values())
        )

        self._actualizar_tabla(
            self.tabla_historico,
            self.escenario.historico
        )

    def _actualizar_tabla(self, tabla, eventos):

        for item in tabla.get_children():
            tabla.delete(item)

        for evento in eventos:

            id_evento = getattr(evento, "id", "")
            fecha = getattr(evento, "fecha_hora", "")
            magnitud = getattr(evento, "magnitud", "")
            profundidad = getattr(evento, "profundidad", "")
            prioridad = getattr(evento, "prioridad", "")
            estado_atencion = getattr(
                evento,
                "estado",
                ""
            )
            estado_catalogo = getattr(
                evento,
                "estado_catalogo",
                ""
            )

            if isinstance(id_evento, int):
                id_mostrar = f"SIS-{id_evento:06d}"
            else:
                id_mostrar = id_evento

            tabla.insert(
                "",
                tk.END,
                values=(
                    id_mostrar,
                    fecha,
                    magnitud,
                    profundidad,
                    prioridad,
                    estado_atencion,
                    estado_catalogo
                )
            )