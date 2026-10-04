import copy
import random
import tkinter as tk
from tkinter import messagebox, ttk

from Modelos import Metricas
from Modelos.AVL import AVL
from Modelos.BST import ArbolBST
from Modelos.Nodo import Nodo

ORDENES = [
    "Por niveles del AVL actual",
    "Ascendente por clave",
    "Descendente por clave",
    "Por identificador",
    "Aleatorio (semilla 42)",
]

DX, DY, RADIO = 38, 56, 17


class VentanaComparativaBST(tk.Toplevel):
    """
    Compares an AVL (balanced) and a BST (unbalanced) built from the SAME
    active events, with the same comparator and the same insertion order.
    The live scenario is never modified (events are inserted as copies).
    """

    def __init__(self, parent, escenario):
        super().__init__(parent)
        self.title("Comparación AVL vs BST")
        self.geometry("1250x820")

        self.escenario = escenario

        if self.escenario.arbol_avl is None or self.escenario.arbol_avl.raiz is None:
            messagebox.showinfo("Sin eventos", "No hay eventos activos para comparar.", parent=parent)
            self.destroy()
            return

        f_top = ttk.Frame(self)
        f_top.pack(fill="x", padx=10, pady=8)
        ttk.Label(f_top, text="Orden de inserción:").pack(side="left", padx=5)
        self.combo_orden = ttk.Combobox(f_top, values=ORDENES, state="readonly", width=32)
        self.combo_orden.current(0)
        self.combo_orden.pack(side="left", padx=5)
        self.combo_orden.bind("<<ComboboxSelected>>", lambda e: self._actualizar())
        ttk.Button(f_top, text="Recalcular", command=self._actualizar).pack(side="left", padx=10)
        self.lbl_info = ttk.Label(f_top, text="", font=("Arial", 9, "bold"))
        self.lbl_info.pack(side="left", padx=15)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas_avl = self._crear_canvas(paned, " AVL (con balanceo) ")
        self.canvas_bst = self._crear_canvas(paned, " BST (sin balanceo) ")

        f_tabla = ttk.LabelFrame(self, text=" Métricas estructurales por orden de inserción ")
        f_tabla.pack(fill="x", padx=10, pady=5)
        columnas = ("orden", "estructura", "nodos", "altura", "hojas", "comp_prom", "comp_max", "comp_total")
        encabezados = ("Orden", "Estructura", "Nodos", "Altura", "Hojas",
                       "Comparaciones (prom.)", "Comparaciones (máx.)", "Comparaciones (total)")
        anchos = (230, 150, 60, 60, 60, 160, 160, 160)
        self.tabla = ttk.Treeview(f_tabla, columns=columnas, show="headings", height=12)
        for col, enc, ancho in zip(columnas, encabezados, anchos):
            self.tabla.heading(col, text=enc)
            self.tabla.column(col, width=ancho, anchor="center")
        self.tabla.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            f_tabla,
            text="Comparaciones = nodos visitados al buscar cada clave almacenada (profundidad + 1). "
                 "Colores: prioridad alta = rojo; borde naranja grueso = acceso costoso.",
            font=("Arial", 8),
        ).pack(anchor="w", padx=5, pady=(0, 5))

        self._actualizar()

    # ------------------------------------------------------------------
    # BUILDING
    # ------------------------------------------------------------------
    def _crear_canvas(self, paned, titulo):
        marco = ttk.LabelFrame(paned, text=titulo)
        paned.add(marco, weight=1)
        canvas = tk.Canvas(marco, bg="white", height=330)
        sb_x = ttk.Scrollbar(marco, orient="horizontal", command=canvas.xview)
        sb_y = ttk.Scrollbar(marco, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=sb_x.set, yscrollcommand=sb_y.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        return canvas

    def _eventos_activos_por_niveles(self):
        raiz = self.escenario.arbol_avl.raiz
        return [n.evento for n in Metricas.nodos_por_niveles(raiz)]

    def _eventos_en_orden(self, nombre):
        eventos = self._eventos_activos_por_niveles()
        if nombre == ORDENES[0]:
            return eventos
        if nombre == ORDENES[1]:
            return sorted(eventos, key=lambda e: e.clave)
        if nombre == ORDENES[2]:
            return sorted(eventos, key=lambda e: e.clave, reverse=True)
        if nombre == ORDENES[3]:
            return sorted(eventos, key=lambda e: e.id)
        mezclados = list(eventos)
        random.Random(42).shuffle(mezclados)
        return mezclados

    def _construir(self, eventos):
        """Same comparator, same order. Shallow copies keep live events untouched."""
        limite_L = self.escenario.L
        avl = AVL(modo_estres=False)
        bst = ArbolBST()
        for evento in eventos:
            avl.insertar(Nodo(evento=copy.copy(evento)), limite_L)
            bst.insertar(copy.copy(evento))
        return avl, bst

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    def _actualizar(self):
        if self.escenario.arbol_avl is None or self.escenario.arbol_avl.raiz is None:
            self.canvas_avl.delete("all")
            self.canvas_bst.delete("all")
            self.lbl_info.config(text="No hay eventos activos.")
            return

        orden = self.combo_orden.get()
        avl, bst = self._construir(self._eventos_en_orden(orden))
        self._dibujar(self.canvas_avl, avl.raiz)
        self._dibujar(self.canvas_bst, bst.raiz)

        m_avl = Metricas.resumen(avl.raiz)
        m_bst = Metricas.resumen(bst.raiz)
        self.lbl_info.config(
            text=f"AVL: altura {m_avl['altura']}, hojas {m_avl['hojas']}  |  "
                 f"BST: altura {m_bst['altura']}, hojas {m_bst['hojas']}"
        )
        self._llenar_tabla()

    def _fila(self, orden, estructura, m):
        return (
            orden, estructura, m["nodos"], m["altura"], m["hojas"],
            f"{m['comparaciones_promedio']:.2f}", m["comparaciones_maximo"], m["comparaciones_total"],
        )

    def _llenar_tabla(self):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        vivo = self.escenario.arbol_avl
        etiqueta = "AVL vivo" + (" (modo estrés)" if vivo.modo_estres else "")
        self.tabla.insert("", "end", values=self._fila("Estado actual del catálogo", etiqueta, Metricas.resumen(vivo.raiz)))

        for orden in ORDENES:
            avl, bst = self._construir(self._eventos_en_orden(orden))
            self.tabla.insert("", "end", values=self._fila(orden, "AVL", Metricas.resumen(avl.raiz)))
            self.tabla.insert("", "end", values=self._fila(orden, "BST", Metricas.resumen(bst.raiz)))

    # ------------------------------------------------------------------
    # DRAWING (iterative, inorder layout: x = inorder index, y = depth)
    # ------------------------------------------------------------------
    @staticmethod
    def _posiciones(raiz):
        posiciones = {}
        pila = []
        actual = raiz
        profundidad = 0
        indice = 0
        while pila or actual is not None:
            while actual is not None:
                pila.append((actual, profundidad))
                actual = actual.izquierda
                profundidad += 1
            actual, profundidad = pila.pop()
            posiciones[id(actual)] = (indice, profundidad)
            indice += 1
            actual = actual.derecha
            profundidad += 1
        return posiciones

    def _dibujar(self, canvas, raiz):
        canvas.delete("all")
        if raiz is None:
            canvas.create_text(150, 80, text="Árbol vacío", fill="gray")
            return

        posiciones = self._posiciones(raiz)

        def xy(nodo):
            indice, profundidad = posiciones[id(nodo)]
            return 30 + indice * DX, 30 + profundidad * DY

        nodos = Metricas.nodos_por_niveles(raiz)
        for nodo in nodos:
            x, y = xy(nodo)
            for hijo in (nodo.izquierda, nodo.derecha):
                if hijo is not None:
                    x2, y2 = xy(hijo)
                    canvas.create_line(x, y, x2, y2, fill="gray", width=1)

        for nodo in nodos:
            x, y = xy(nodo)
            evento = nodo.evento
            fondo, borde, grosor = "#E1F5FE", "#0288D1", 2
            if evento.prioridad == 3:
                fondo, borde = "#FFCDD2", "#C62828"
            if getattr(evento, "acceso_costoso", False):
                borde, grosor = "#FF8F00", 4
            canvas.create_oval(x - RADIO, y - RADIO, x + RADIO, y + RADIO, fill=fondo, outline=borde, width=grosor)
            canvas.create_text(x, y, text=str(evento.id), font=("Arial", 7, "bold"))

        canvas.configure(scrollregion=canvas.bbox("all"))