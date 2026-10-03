import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Ventana emergente para desplegar detalles al pasar el cursor sobre un objeto."""
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
        self.geometry("900x720")
        
        self.escenario = escenario
        self.tooltip = ToolTip(self)
        
        # Dimensiones del Canvas
        self.ancho_canvas = 800
        self.alto_canvas = 600
        self.margen = 50
        
        # Límites por defecto (se auto-calculan en dibujar_plano)
        self.x_min_geo, self.x_max_geo = 0.0, 1000.0
        self.y_min_geo, self.y_max_geo = 0.0, 1000.0
        
        self.crear_interfaz()
        self.dibujar_plano()

    def crear_interfaz(self):
        f_top = ttk.Frame(self)
        f_top.pack(fill=tk.X, padx=20, pady=8)

        lbl_titulo = ttk.Label(
            f_top, 
            text="Plano Geográfico: Pasa el cursor sobre Zonas, Estaciones o Epicentros", 
            font=("Arial", 11, "bold")
        )
        lbl_titulo.pack(side=tk.LEFT)

        btn_refrescar = ttk.Button(
            f_top,
            text="Refrescar Mapa",
            command=self.dibujar_plano
        )
        btn_refrescar.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(
            self, width=self.ancho_canvas, height=self.alto_canvas,
            bg="#F5F5F5", highlightthickness=1, highlightbackground="gray"
        )
        self.canvas.pack(padx=20, pady=5)

    def geo_a_pixel(self, x_geo, y_geo):
        """Mapea coordenadas geográficas a píxeles con inversión de eje Y."""
        ancho_util = self.ancho_canvas - (2 * self.margen)
        alto_util = self.alto_canvas - (2 * self.margen)
        
        dx = self.x_max_geo - self.x_min_geo
        dy = self.y_max_geo - self.y_min_geo
        if dx == 0: dx = 1.0
        if dy == 0: dy = 1.0

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

    def _extraer_xy(self, obj):
        """Extrae (x, y) de diccionarios o de instancias de clase."""
        if isinstance(obj, dict):
            return float(obj.get("x", 0)), float(obj.get("y", 0))
        return float(getattr(obj, "x", 0)), float(getattr(obj, "y", 0))

    def _obtener_datos_escenario(self):
        """Extrae las colecciones directamente desde las variables de la clase Escenario."""
        zonas = getattr(self.escenario, "zonas", [])
        estaciones = getattr(self.escenario, "estaciones", [])
        epicentros = getattr(self.escenario, "epicentros", [])
        
        dict_eventos = getattr(self.escenario, "dict_eventos", {})
        if isinstance(dict_eventos, dict):
            eventos = list(dict_eventos.values())
        else:
            eventos = []

        return zonas, estaciones, epicentros, eventos

    def _obtener_info_zona_epicentro(self, ep):
        """Lee directamente el objeto zona asignado al epicentro y determina si es poblada."""
        # 1. Si el epicentro es una instancia de la clase Epicentro
        if hasattr(ep, "zona"):
            zona_obj = ep.zona
            if zona_obj:
                nombre_zona = getattr(zona_obj, "nombre", "Sin Nombre")
                es_poblada = getattr(zona_obj, "poblada", False)
                txt_poblada = "Sí (Zona Poblada)" if es_poblada else "No (Zona No Poblada)"
                return nombre_zona, txt_poblada
            return "Sin Zona Asignada", "No"

        # 2. Si el epicentro es un diccionario
        if isinstance(ep, dict):
            zona_obj = ep.get("zona")
            if isinstance(zona_obj, dict):
                nombre_zona = zona_obj.get("nombre", "Sin Nombre")
                es_poblada = zona_obj.get("poblada", False)
                txt_poblada = "Sí (Zona Poblada)" if es_poblada else "No (Zona No Poblada)"
                return nombre_zona, txt_poblada
            elif zona_obj:
                nombre_zona = getattr(zona_obj, "nombre", "Sin Nombre")
                es_poblada = getattr(zona_obj, "poblada", False)
                txt_poblada = "Sí (Zona Poblada)" if es_poblada else "No (Zona No Poblada)"
                return nombre_zona, txt_poblada

        return "Sin Zona Asignada", "No"

    def _calcular_limites_geograficos(self, zonas, estaciones, epicentros):
        """Ajusta la escala automáticamente para que todo quepa en el Canvas."""
        xs, ys = [], []

        for z in zonas:
            z_dict = z if isinstance(z, dict) else getattr(z, "__dict__", {})
            xs.extend([float(z_dict.get("x_min", 0)), float(z_dict.get("x_max", 0))])
            ys.extend([float(z_dict.get("y_min", 0)), float(z_dict.get("y_max", 0))])

        for est in estaciones:
            x, y = self._extraer_xy(est)
            xs.append(x)
            ys.append(y)

        for ep in epicentros:
            x, y = self._extraer_xy(ep)
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

    def dibujar_plano(self):
        self.canvas.delete("all")
        zonas, estaciones, epicentros, eventos = self._obtener_datos_escenario()

        self._calcular_limites_geograficos(zonas, estaciones, epicentros)

        # 1. DIBUJAR ZONAS GEOGRÁFICAS
        for z in zonas:
            z_dict = z if isinstance(z, dict) else getattr(z, "__dict__", {})
            x_min = float(z_dict.get("x_min", 0))
            x_max = float(z_dict.get("x_max", 0))
            y_min = float(z_dict.get("y_min", 0))
            y_max = float(z_dict.get("y_max", 0))
            
            x1, y1 = self.geo_a_pixel(x_min, y_min)
            x2, y2 = self.geo_a_pixel(x_max, y_max)
            
            poblada = getattr(z, 'poblada', z_dict.get("poblada", False))
            nombre = getattr(z, 'nombre', z_dict.get("nombre", 'N/A'))
            color_zona = "#FFEBEB" if poblada else "#EBFEEB"
            
            rect_id = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color_zona, outline="#888888", width=1, dash=(4, 2)
            )
            
            info_zona = (
                f"Zona: {nombre}\n"
                f"Poblada: {'Sí' if poblada else 'No'}\n"
                f"Rango X: [{x_min}, {x_max}]\n"
                f"Rango Y: [{y_min}, {y_max}]"
            )
            self.vincular_tooltip(rect_id, info_zona)

        # 2. DIBUJAR ESTACIONES DE MONITOREO
        for est in estaciones:
            ex, ey = self._extraer_xy(est)
            px, py = self.geo_a_pixel(ex, ey)
            r = 8
            
            e_dict = est if isinstance(est, dict) else getattr(est, "__dict__", {})
            nombre_est = getattr(est, 'nombre', e_dict.get('nombre', e_dict.get('id_estacion', 'Estación')))
            id_est = getattr(est, 'id_estacion', e_dict.get('id_estacion', 'N/A'))
            
            est_id = self.canvas.create_polygon(
                [px, py - r, px + r, py, px, py + r, px - r, py],
                fill="#1E88E5", outline="black", width=1
            )
            
            info_estacion = f"Estación: {nombre_est}\nID: {id_est}\nPosición: ({ex}, {ey})"
            self.vincular_tooltip(est_id, info_estacion)

        # 3. AGRUPAR EVENTOS POR SUS COORDENADAS DE EPICENTRO
        eventos_por_coordenada = {}
        for ev in eventos:
            ev_dict = ev if isinstance(ev, dict) else getattr(ev, "__dict__", {})
            ep_obj = getattr(ev, 'epicentro', ev_dict.get("epicentro", {}))
            ev_x, ev_y = self._extraer_xy(ep_obj)
            
            clave_pos = (round(ev_x, 1), round(ev_y, 1))
            if clave_pos not in eventos_por_coordenada:
                eventos_por_coordenada[clave_pos] = []
            eventos_por_coordenada[clave_pos].append(ev)

        # 4. DIBUJAR EPICENTROS (USA EPICENTRO.ZONA Y ZONA.POBLADA)
        for ep in epicentros:
            ep_x, ep_y = self._extraer_xy(ep)
            px, py = self.geo_a_pixel(ep_x, ep_y)
            clave_ep = (round(ep_x, 1), round(ep_y, 1))
            
            # Obtener zona y estado poblado a través del objeto epicentro
            nombre_zona, txt_poblada = self._obtener_info_zona_epicentro(ep)

            eventos_asociados = eventos_por_coordenada.get(clave_ep, [])

            if eventos_asociados:
                eventos_ordenados = sorted(
                    eventos_asociados, 
                    key=lambda e: float(getattr(e, 'magnitud', e.get('magnitud', 0) if isinstance(e, dict) else 0)), 
                    reverse=True
                )
                
                evento_max = eventos_ordenados[0]
                mag_max = float(getattr(evento_max, 'magnitud', 0.0) if not isinstance(evento_max, dict) else evento_max.get('magnitud', 0.0))
                
                hay_pendiente = any(
                    (getattr(ev, 'estado_atencion', 'Pendiente') if not isinstance(ev, dict) else ev.get('estado_atencion', 'Pendiente')) == "Pendiente"
                    for ev in eventos_asociados
                )
                color = "#D32F2F" if hay_pendiente else "#388E3C"
                radio = max(int(mag_max * 3), 7)
                
                ep_id = self.canvas.create_oval(
                    px - radio, py - radio, px + radio, py + radio,
                    fill=color, outline="yellow", width=2
                )
                
                lineas_info = [
                    f"EPICENTRO: ({ep_x}, {ep_y})",
                    f"Zona Asignada: {nombre_zona}",
                    f"¿Zona Poblada?: {txt_poblada}",
                    f"Total de sismos registrados: {len(eventos_asociados)}",
                    "-" * 32
                ]
                
                for idx, ev in enumerate(eventos_ordenados, start=1):
                    is_dict = isinstance(ev, dict)
                    id_ev = getattr(ev, 'id', getattr(ev, 'id_evento', 'N/A')) if not is_dict else ev.get('id_evento', ev.get('id', 'N/A'))
                    mag = getattr(ev, 'magnitud', 'N/A') if not is_dict else ev.get('magnitud', 'N/A')
                    prof = getattr(ev, 'profundidad', 'N/A') if not is_dict else ev.get('profundidad', 'N/A')
                    estado = getattr(ev, 'estado_atencion', 'N/A') if not is_dict else ev.get('estado_atencion', 'N/A')
                    fecha = getattr(ev, 'fecha_hora', 'N/A') if not is_dict else ev.get('fecha_hora', 'N/A')
                    
                    lineas_info.append(
                        f"#{idx} | ID: {id_ev}\n"
                        f"   • Magnitud: {mag} Mw | Prof: {prof} km\n"
                        f"   • Estado: {estado}\n"
                        f"   • Fecha: {fecha}"
                    )
                
                info_ep = "\n".join(lineas_info)
            else:
                radio = 4
                ep_id = self.canvas.create_oval(
                    px - radio, py - radio, px + radio, py + radio,
                    fill="#757575", outline="black", width=1
                )
                info_ep = (
                    f"Epicentro Monitoreado (Sin Evento)\n"
                    f"Posición: ({ep_x}, {ep_y})\n"
                    f"Zona Asignada: {nombre_zona}\n"
                    f"¿Zona Poblada?: {txt_poblada}"
                )

            self.vincular_tooltip(ep_id, info_ep)