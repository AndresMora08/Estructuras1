import tkinter as tk
from tkinter import ttk

from Modelos import Metricas


RADIO = 18
DX = 55
DY = 70


class VentanaComparativaBST(tk.Toplevel):
    """
    Muestra lado a lado el AVL y el BST reales del escenario.

    El AVL corresponde a escenario.arbol_avl.
    El BST corresponde a escenario.arbol_bst.

    Esta ventana solamente consulta y dibuja los árboles.
    No modifica el escenario.
    """

    def __init__(self, parent, escenario):
        super().__init__(parent)

        self.parent = parent
        self.escenario = escenario

        self.title("Comparación AVL vs BST")
        self.geometry("1350x750")
        self.minsize(1000, 600)

        self._crear_interfaz()
        self._actualizar()

    # ==============================================================
    # INTERFAZ
    # ==============================================================

    def _crear_interfaz(self):

        marco_superior = ttk.Frame(self)
        marco_superior.pack(
            fill="x",
            padx=10,
            pady=10
        )

        ttk.Label(
            marco_superior,
            text="Comparación de estructuras",
            font=("Arial", 14, "bold")
        ).pack(
            side="left"
        )

        ttk.Button(
            marco_superior,
            text="Actualizar",
            command=self._actualizar
        ).pack(
            side="right"
        )

        marco_arboles = ttk.Frame(self)
        marco_arboles.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        marco_avl = ttk.LabelFrame(
            marco_arboles,
            text=" AVL del escenario "
        )

        marco_avl.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        marco_bst = ttk.LabelFrame(
            marco_arboles,
            text=" BST del escenario "
        )

        marco_bst.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(5, 0)
        )

        self.canvas_avl = self._crear_canvas(
            marco_avl
        )

        self.canvas_bst = self._crear_canvas(
            marco_bst
        )

        # ==========================================================
        # MÉTRICAS
        # ==========================================================

        marco_metricas = ttk.LabelFrame(
            self,
            text=" Métricas estructurales "
        )

        marco_metricas.pack(
            fill="x",
            padx=10,
            pady=10
        )

        marco_avl_metricas = ttk.LabelFrame(
            marco_metricas,
            text=" AVL "
        )

        marco_avl_metricas.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
            pady=5
        )

        marco_bst_metricas = ttk.LabelFrame(
            marco_metricas,
            text=" BST "
        )

        marco_bst_metricas.pack(
            side="right",
            fill="x",
            expand=True,
            padx=5,
            pady=5
        )

        self.lbl_metricas_avl = ttk.Label(
            marco_avl_metricas,
            text="AVL: --",
            font=("Arial", 9),
            justify="left"
        )

        self.lbl_metricas_avl.pack(
            anchor="w",
            padx=10,
            pady=8
        )

        self.lbl_metricas_bst = ttk.Label(
            marco_bst_metricas,
            text="BST: --",
            font=("Arial", 9),
            justify="left"
        )

        self.lbl_metricas_bst.pack(
            anchor="w",
            padx=10,
            pady=8
        )

    def _crear_canvas(self, padre):

        marco = ttk.Frame(padre)

        marco.pack(
            fill="both",
            expand=True
        )

        canvas = tk.Canvas(
            marco,
            background="white"
        )

        scrollbar_vertical = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=canvas.yview
        )

        scrollbar_horizontal = ttk.Scrollbar(
            marco,
            orient="horizontal",
            command=canvas.xview
        )

        canvas.configure(
            yscrollcommand=scrollbar_vertical.set,
            xscrollcommand=scrollbar_horizontal.set
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar_vertical.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        scrollbar_horizontal.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        marco.rowconfigure(
            0,
            weight=1
        )

        marco.columnconfigure(
            0,
            weight=1
        )

        return canvas

    # ==============================================================
    # ACTUALIZAR
    # ==============================================================

    def _actualizar(self):

        self.canvas_avl.delete("all")
        self.canvas_bst.delete("all")

        arbol_avl = self.escenario.arbol_avl
        arbol_bst = self.escenario.arbol_bst

        if arbol_avl is None:
            self._dibujar_mensaje(
                self.canvas_avl,
                "No existe AVL"
            )
        else:
            self._dibujar_arbol(
                self.canvas_avl,
                arbol_avl.raiz
            )

        if arbol_bst is None:
            self._dibujar_mensaje(
                self.canvas_bst,
                "No existe BST"
            )
        else:
            self._dibujar_arbol(
                self.canvas_bst,
                arbol_bst.raiz
            )

        self._actualizar_metricas(
            arbol_avl,
            arbol_bst
        )

    # ==============================================================
    # MÉTRICAS
    # ==============================================================

    def _actualizar_metricas(
        self,
        arbol_avl,
        arbol_bst
    ):

        if (
            arbol_avl is None
            or arbol_avl.raiz is None
        ):

            texto_avl = "AVL: árbol vacío"

        else:

            metricas_avl = Metricas.resumen(
                arbol_avl.raiz
            )

            texto_avl = (
                f"Nodos: {metricas_avl['nodos']}\n"
                f"Altura: {metricas_avl['altura']}\n"
                f"Hojas: {metricas_avl['hojas']}\n"
                f"Comparaciones promedio: "
                f"{metricas_avl['comparaciones_promedio']:.2f}\n"
                f"Comparaciones máximas: "
                f"{metricas_avl['comparaciones_maximo']}\n"
                f"Comparaciones totales: "
                f"{metricas_avl['comparaciones_total']}"
            )

        if (
            arbol_bst is None
            or arbol_bst.raiz is None
        ):

            texto_bst = "BST: árbol vacío"

        else:

            metricas_bst = Metricas.resumen(
                arbol_bst.raiz
            )

            texto_bst = (
                f"Nodos: {metricas_bst['nodos']}\n"
                f"Altura: {metricas_bst['altura']}\n"
                f"Hojas: {metricas_bst['hojas']}\n"
                f"Comparaciones promedio: "
                f"{metricas_bst['comparaciones_promedio']:.2f}\n"
                f"Comparaciones máximas: "
                f"{metricas_bst['comparaciones_maximo']}\n"
                f"Comparaciones totales: "
                f"{metricas_bst['comparaciones_total']}"
            )

        self.lbl_metricas_avl.config(
            text=texto_avl
        )

        self.lbl_metricas_bst.config(
            text=texto_bst
        )

    # ==============================================================
    # DIBUJAR ÁRBOL
    # ==============================================================

    def _dibujar_arbol(
        self,
        canvas,
        raiz
    ):

        if raiz is None:
            self._dibujar_mensaje(
                canvas,
                "Árbol vacío"
            )
            return

        posiciones = {}

        self._calcular_posiciones(
            raiz,
            posiciones,
            0,
            0
        )

        # ----------------------------------------------------------
        # Líneas
        # ----------------------------------------------------------

        self._dibujar_conexiones(
            canvas,
            raiz,
            posiciones
        )

        # ----------------------------------------------------------
        # Nodos
        # ----------------------------------------------------------

        self._dibujar_nodos(
            canvas,
            raiz,
            posiciones
        )

        # ----------------------------------------------------------
        # Área desplazable
        # ----------------------------------------------------------

        bbox = canvas.bbox("all")

        if bbox is not None:
            margen = 50

            canvas.configure(
                scrollregion=(
                    bbox[0] - margen,
                    bbox[1] - margen,
                    bbox[2] + margen,
                    bbox[3] + margen
                )
            )

    # ==============================================================
    # POSICIONES
    # ==============================================================

    def _calcular_posiciones(
        self,
        nodo,
        posiciones,
        profundidad,
        contador
    ):

        if nodo is None:
            return contador

        contador = self._calcular_posiciones(
            nodo.izquierda,
            posiciones,
            profundidad + 1,
            contador
        )

        posiciones[id(nodo)] = (
            contador,
            profundidad
        )

        contador += 1

        contador = self._calcular_posiciones(
            nodo.derecha,
            posiciones,
            profundidad + 1,
            contador
        )

        return contador

    def _obtener_coordenadas(
        self,
        nodo,
        posiciones
    ):

        indice, profundidad = posiciones[
            id(nodo)
        ]

        x = 60 + indice * DX
        y = 60 + profundidad * DY

        return x, y

    # ==============================================================
    # CONEXIONES
    # ==============================================================

    def _dibujar_conexiones(
        self,
        canvas,
        nodo,
        posiciones
    ):

        if nodo is None:
            return

        x, y = self._obtener_coordenadas(
            nodo,
            posiciones
        )

        if nodo.izquierda is not None:

            x2, y2 = self._obtener_coordenadas(
                nodo.izquierda,
                posiciones
            )

            canvas.create_line(
                x,
                y,
                x2,
                y2,
                fill="gray",
                width=2
            )

        if nodo.derecha is not None:

            x2, y2 = self._obtener_coordenadas(
                nodo.derecha,
                posiciones
            )

            canvas.create_line(
                x,
                y,
                x2,
                y2,
                fill="gray",
                width=2
            )

        self._dibujar_conexiones(
            canvas,
            nodo.izquierda,
            posiciones
        )

        self._dibujar_conexiones(
            canvas,
            nodo.derecha,
            posiciones
        )

    # ==============================================================
    # NODOS
    # ==============================================================

    def _dibujar_nodos(
        self,
        canvas,
        nodo,
        posiciones
    ):

        if nodo is None:
            return

        x, y = self._obtener_coordenadas(
            nodo,
            posiciones
        )

        evento = nodo.evento

        # Color normal del nodo
        fondo = "#E8F4FD"
        borde = "#1976D2"
        ancho = 2

        # Prioridad alta
        if getattr(
            evento,
            "prioridad",
            0
        ) == 3:

            fondo = "#FFCDD2"
            borde = "#C62828"

        canvas.create_oval(
            x - RADIO,
            y - RADIO,
            x + RADIO,
            y + RADIO,
            fill=fondo,
            outline=borde,
            width=ancho
        )

        # ID del evento
        canvas.create_text(
            x,
            y,
            text=str(evento.id),
            font=("Arial", 8, "bold")
        )

        self._dibujar_nodos(
            canvas,
            nodo.izquierda,
            posiciones
        )

        self._dibujar_nodos(
            canvas,
            nodo.derecha,
            posiciones
        )

    # ==============================================================
    # MENSAJE ÁRBOL VACÍO
    # ==============================================================

    def _dibujar_mensaje(
        self,
        canvas,
        mensaje
    ):

        canvas.create_text(
            200,
            100,
            text=mensaje,
            fill="gray",
            font=("Arial", 12, "bold")
        )

        canvas.configure(
            scrollregion=(0, 0, 500, 300)
        )