import tkinter as tk
from tkinter import ttk

MAX_EVENTOS_TOOLTIP = 8


class ToolTip:
    """Pop-up window with details while the cursor is over an object."""
    def __init__(self, canvas):
        self.canvas = canvas
        self.tip_window = None

    def mostrar(self, texto, x_root, y_root):
        self.ocultar()
        self.tip_window = tw = tk.Toplevel(self.canvas)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x_root + 15}+{y_root + 10}")

        label = tk.Label(
            tw, text=texto, justify=tk.LEFT,
            background="#FFFFE1", relief=tk.SOLID, borderwidth=1,
            font=("Arial", 9, "normal"), padx=6, pady=4
        )
        label.pack()

    def ocultar(self):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class Mapa(tk.Toplevel):
    def __init__(self, parent, escenario):
        super().__init__(parent)
        self.title("Plano Geográfico Interactivo - SismoLab")
        self.geometry("900x740")

        self.escenario = escenario
        self.tooltip = ToolTip(self)

        self.ancho_canvas = 800
        self.alto_canvas = 600
        self.margen = 50

        self.x_min_geo, self.x_max_geo = 0.0, 1000.0
        self.y_min_geo, self.y_max_geo = 0.0, 1000.0

        self.crear_interfaz()
        self.dibujar_plano()

    def crear_interfaz(self):
        f_top = ttk.Frame(self)
        f_top.pack(fill=tk.X, padx=20, pady=8)

        ttk.Label(
            f_top,
            text="Plano Geográfico: pasa el cursor sobre Zonas, Estaciones o Epicentros",
            font=("Arial", 11, "bold")
        ).pack(side=tk.LEFT)

        ttk.Button(f_top, text="Refrescar Mapa", command=self.dibujar_plano).pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(
            self, width=self.ancho_canvas, height=self.alto_canvas,
            bg="#F5F5F5", highlightthickness=1, highlightbackground="gray"
        )
        self.canvas.pack(padx=20, pady=5)

        ttk.Label(
            self,
            text=("Leyenda: círculo rojo = epicentro con eventos pendientes | verde = todos revisados | "
                  "gris = sin eventos | el radio crece con la magnitud | rombo azul = estación | "
                  "zona rosa = poblada, verde claro = no poblada"),
            font=("Arial", 8), wraplength=860, justify=tk.LEFT
        ).pack(padx=20, pady=(0, 8))

    def geo_a_pixel(self, x_geo, y_geo):
        """Maps km coordinates to pixels (Y axis is inverted)."""
        ancho_util = self.ancho_canvas - (2 * self.margen)
        alto_util = self.alto_canvas - (2 * self.margen)

        dx = self.x_max_geo - self.x_min_geo
        dy = self.y_max_geo - self.y_min_geo
        if dx == 0:
            dx = 1.0
        if dy == 0:
            dy = 1.0

        px = self.margen + ((x_geo - self.x_min_geo) / dx) * ancho_util
        py = (self.alto_canvas - self.margen) - ((y_geo - self.y_min_geo) / dy) * alto_util
        return px, py

    def vincular_tooltip(self, id_item, texto_info):
        def en_hover(event):
            self.tooltip.mostrar(texto_info, event.x_root, event.y_root)

        def en_leave(event):
            self.tooltip.ocultar()

        self.canvas.tag_bind(id_item, "<Enter>", en_hover)
        self.canvas.tag_bind(id_item, "<Leave>", en_leave)

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def _obtener_datos_escenario(self):
        zonas = list(getattr(self.escenario, "zonas", []) or [])
        estaciones = list(getattr(self.escenario, "estaciones", []) or [])
        epicentros = list(getattr(self.escenario, "epicentros", []) or [])
        dict_eventos = getattr(self.escenario, "dict_eventos", {}) or {}
        eventos = list(dict_eventos.values())
        return zonas, estaciones, epicentros, eventos

    @staticmethod
    def _clave_pos(x, y):
        return (round(float(x), 1), round(float(y), 1))

    def _puntos_epicentro(self, epicentros, eventos):
        """
        Epicenters to draw: the ones of the scenario plus the ones of events whose
        coordinates are not registered as a scenario epicenter (e.g. loaded from JSON).
        """
        puntos = {}
        for ep in epicentros:
            puntos.setdefault(self._clave_pos(ep.x, ep.y), ep)
        for ev in eventos:
            if ev.epicentro is not None:
                puntos.setdefault(self._clave_pos(ev.epicentro.x, ev.epicentro.y), ev.epicentro)
        return puntos

    @staticmethod
    def _info_zona_epicentro(ep):
        zona = getattr(ep, "zona", None)
        if zona is None:
            return "Sin Zona Asignada", "No"
        return zona.nombre, "Sí (Zona Poblada)" if zona.poblada else "No (Zona No Poblada)"

    def _calcular_limites_geograficos(self, zonas, estaciones, puntos):
        xs, ys = [], []
        for z in zonas:
            xs.extend([z.x_min, z.x_max])
            ys.extend([z.y_min, z.y_max])
        for est in estaciones:
            xs.append(est.x)
            ys.append(est.y)
        for (x, y) in puntos:
            xs.append(x)
            ys.append(y)

        if xs and ys:
            self.x_min_geo, self.x_max_geo = min(xs), max(xs)
            self.y_min_geo, self.y_max_geo = min(ys), max(ys)
            if self.x_min_geo == self.x_max_geo:
                self.x_max_geo += 100
            if self.y_min_geo == self.y_max_geo:
                self.y_max_geo += 100
        else:
            self.x_min_geo, self.x_max_geo = 0.0, 1000.0
            self.y_min_geo, self.y_max_geo = 0.0, 1000.0

    # ------------------------------------------------------------------
    # DRAWING
    # ------------------------------------------------------------------
    def dibujar_plano(self):
        self.canvas.delete("all")
        zonas, estaciones, epicentros, eventos = self._obtener_datos_escenario()
        puntos = self._puntos_epicentro(epicentros, eventos)

        self._calcular_limites_geograficos(zonas, estaciones, puntos)

        # 1. ZONES
        for z in zonas:
            x1, y1 = self.geo_a_pixel(z.x_min, z.y_min)
            x2, y2 = self.geo_a_pixel(z.x_max, z.y_max)
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#FFEBEB" if z.poblada else "#EBFEEB",
                outline="#888888", width=1, dash=(4, 2)
            )
            self.vincular_tooltip(
                rect_id,
                f"Zona: {z.nombre}\n"
                f"Poblada: {'Sí' if z.poblada else 'No'}\n"
                f"Rango X: [{z.x_min}, {z.x_max}]\n"
                f"Rango Y: [{z.y_min}, {z.y_max}]"
            )

        # 2. STATIONS
        r = 8
        for est in estaciones:
            px, py = self.geo_a_pixel(est.x, est.y)
            est_id = self.canvas.create_polygon(
                [px, py - r, px + r, py, px, py + r, px - r, py],
                fill="#1E88E5", outline="black", width=1
            )
            self.vincular_tooltip(
                est_id,
                f"Estación: {est.nombre}\nID: {est.id_estacion}\nPosición: ({est.x}, {est.y})"
            )

        # 3. GROUP EVENTS BY EPICENTER COORDINATES
        eventos_por_coordenada = {}
        for ev in eventos:
            if ev.epicentro is None:
                continue
            clave = self._clave_pos(ev.epicentro.x, ev.epicentro.y)
            eventos_por_coordenada.setdefault(clave, []).append(ev)

        # 4. EPICENTERS
        for clave_ep, ep in puntos.items():
            ep_x, ep_y = clave_ep
            px, py = self.geo_a_pixel(ep_x, ep_y)
            nombre_zona, txt_poblada = self._info_zona_epicentro(ep)
            asociados = eventos_por_coordenada.get(clave_ep, [])

            if asociados:
                ordenados = sorted(asociados, key=lambda e: e.magnitud, reverse=True)
                mag_max = ordenados[0].magnitud
                hay_pendiente = any(e.estado == "Pendiente" for e in asociados)
                color = "#D32F2F" if hay_pendiente else "#388E3C"
                radio = max(int(mag_max * 3), 7)

                ep_id = self.canvas.create_oval(
                    px - radio, py - radio, px + radio, py + radio,
                    fill=color, outline="yellow", width=2
                )

                lineas = [
                    f"EPICENTRO: ({ep_x}, {ep_y})",
                    f"Zona Asignada: {nombre_zona}",
                    f"¿Zona Poblada?: {txt_poblada}",
                    f"Total de sismos registrados: {len(asociados)}",
                    "-" * 32,
                ]
                for idx, ev in enumerate(ordenados[:MAX_EVENTOS_TOOLTIP], start=1):
                    lineas.append(
                        f"#{idx} | SIS-{ev.id:06d} | Prioridad {ev.prioridad}\n"
                        f"   • Magnitud: {ev.magnitud} Mw | Prof: {ev.profundidad} km\n"
                        f"   • Estado: {ev.estado}\n"
                        f"   • Fecha: {ev.fecha_hora}"
                    )
                if len(ordenados) > MAX_EVENTOS_TOOLTIP:
                    lineas.append(f"... y {len(ordenados) - MAX_EVENTOS_TOOLTIP} más")
                info_ep = "\n".join(lineas)
            else:
                radio = 4
                ep_id = self.canvas.create_oval(
                    px - radio, py - radio, px + radio, py + radio,
                    fill="#757575", outline="black", width=1
                )
                info_ep = (
                    "Epicentro Monitoreado (Sin Evento)\n"
                    f"Posición: ({ep_x}, {ep_y})\n"
                    f"Zona Asignada: {nombre_zona}\n"
                    f"¿Zona Poblada?: {txt_poblada}"
                )

            self.vincular_tooltip(ep_id, info_ep)