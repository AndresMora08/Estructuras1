import json
from datetime import datetime, timezone
from typing import Dict, List, Any
from tkinter import filedialog, messagebox

from Modelos.Evento import Evento
from Modelos.Epicentro import Epicentro
from Modelos.Zona import Zona
from Modelos.Estacion import Estacion
from Modelos.Nodo import Nodo


class ControladorJSON:
    FORMATO_ISO = "%Y-%m-%dT%H:%M:%SZ"

    # =========================================================================
    # VALIDACIONES DE PARÁMETROS SEGÚN ESPECIFICACIÓN
    # =========================================================================

    @staticmethod
    def _validar_decimal_max_un_decimal(valor: float, nombre_campo: str):
        """Valida que el número no tenga más de un dígito decimal."""
        val_round = round(valor, 4)
        if round(val_round, 1) != val_round:
            raise ValueError(f"El campo '{nombre_campo}' ({valor}) tiene más de 1 decimal permitido.")

    @classmethod
    def validar_datos_evento(cls, d: Dict[str, Any]):
        """Valida rigurosamente que el diccionario JSON cumpla con las reglas de negocio."""
        # 1. Identificador: Entero entre 1 y 999999
        id_val = d.get("id")
        if not isinstance(id_val, int) or isinstance(id_val, bool):
            raise ValueError(f"El ID de evento debe ser un número entero. Recibido: {id_val}")
        if not (1 <= id_val <= 999999):
            raise ValueError(f"El ID de evento debe estar entre 1 y 999999. Recibido: {id_val}")

        # 2. Magnitud M: Decimal finito entre -2.0 y 10.0, máximo 1 decimal
        mag_val = d.get("magnitud")
        if not isinstance(mag_val, (int, float)) or isinstance(mag_val, bool):
            raise ValueError(f"La magnitud debe ser un número. Recibido: {mag_val}")
        mag_float = float(mag_val)
        if not (-2.0 <= mag_float <= 10.0):
            raise ValueError(f"La magnitud ({mag_float}) debe estar entre -2.0 y 10.0")
        cls._validar_decimal_max_un_decimal(mag_float, "magnitud")

        # 3. Profundidad H: Decimal entre 0.0 y 700.0 km, máximo 1 decimal
        prof_val = d.get("profundidad")
        if not isinstance(prof_val, (int, float)) or isinstance(prof_val, bool):
            raise ValueError(f"La profundidad debe ser un número. Recibido: {prof_val}")
        prof_float = float(prof_val)
        if not (0.0 <= prof_float <= 700.0):
            raise ValueError(f"La profundidad ({prof_float}) debe estar entre 0.0 y 700.0 km")
        cls._validar_decimal_max_un_decimal(prof_float, "profundidad")

        # 4. Epicentro: x e y en km entre 0.0 y 1000.0, máximo 1 decimal
        epi_dict = d.get("epicentro")
        if not isinstance(epi_dict, dict):
            raise ValueError("El objeto 'epicentro' es obligatorio.")
        
        for coord_key in ["x", "y"]:
            if coord_key not in epi_dict:
                raise ValueError(f"Falta la coordenada '{coord_key}' en el epicentro.")
            c_val = epi_dict[coord_key]
            if not isinstance(c_val, (int, float)) or isinstance(c_val, bool):
                raise ValueError(f"La coordenada epicentro '{coord_key}' debe ser numérica. Recibido: {c_val}")
            c_float = float(c_val)
            if not (0.0 <= c_float <= 1000.0):
                raise ValueError(f"La coordenada epicentro '{coord_key}' ({c_float}) debe estar entre 0.0 y 1000.0 km")
            cls._validar_decimal_max_un_decimal(c_float, f"epicentro.{coord_key}")

        # 5. Revisión: Entera positiva (>= 1)
        rev_val = d.get("revision")
        if not isinstance(rev_val, int) or isinstance(rev_val, bool) or rev_val < 1:
            raise ValueError(f"La revisión debe ser un número entero positivo (>= 1). Recibido: {rev_val}")

        # 6. Estación origen
        id_est = d.get("estacion_origen")
        if not id_est or not isinstance(id_est, str):
            raise ValueError("La estación que emite el reporte ('estacion_origen') es obligatoria.")

        # 7. Estado de atención: Debe ser 'Pendiente' o 'Revisado'
        estado_val = d.get("estado")
        if estado_val not in ["Pendiente", "Revisado"]:
            raise ValueError(f"El estado de atención debe ser 'Pendiente' o 'Revisado'. Recibido: '{estado_val}'")

    # =========================================================================
    # DICCIONARIO <-> OBJETOS
    # =========================================================================

    @classmethod
    def dict_a_evento(cls, d: Dict[str, Any], escenario: Any = None) -> Evento:
        cls.validar_datos_evento(d)

        id_evento = int(d["id"])
        zonas_escenario: List[Zona] = getattr(escenario, "zonas", []) if escenario else []

        epi_dict = d["epicentro"]
        x_epi = float(epi_dict["x"])
        y_epi = float(epi_dict["y"])

        # 1. Registrar / Crear Zona si viene definida
        if "zona" in epi_dict and isinstance(epi_dict["zona"], dict):
            z_data = epi_dict["zona"]
            nombre_z = str(z_data.get("nombre", "Zona Defecto"))

            zona_existente = next((z for z in zonas_escenario if z.nombre == nombre_z), None)

            if not zona_existente:
                nueva_zona = Zona(
                    nombre=nombre_z,
                    x_min=float(z_data.get("x_min", 0.0)),
                    x_max=float(z_data.get("x_max", 1000.0)),
                    y_min=float(z_data.get("y_min", 0.0)),
                    y_max=float(z_data.get("y_max", 1000.0)),
                    poblada=bool(z_data.get("poblada", False)),
                )
                if escenario and hasattr(escenario, "zonas") and isinstance(escenario.zonas, list):
                    escenario.zonas.append(nueva_zona)
                zonas_escenario.append(nueva_zona)

        # 2. Crear Epicentro
        epicentro = Epicentro(x_epi, y_epi, zonas_escenario)

        if escenario and hasattr(escenario, "epicentros") and isinstance(escenario.epicentros, list):
            escenario.epicentros.append(epicentro)

        # 3. Registrar / Crear Estación
        id_est = str(d["estacion_origen"])
        est_dict = d.get("estacion_origen_datos", {})

        estaciones_escenario = getattr(escenario, "estaciones", []) if escenario else []
        mapa_estaciones = {
            e.id_estacion: e for e in estaciones_escenario if isinstance(e, Estacion)
        } if estaciones_escenario else {}

        if id_est in mapa_estaciones:
            estacion_obj = mapa_estaciones[id_est]
        else:
            x_est = float(est_dict.get("x", x_epi))
            y_est = float(est_dict.get("y", y_epi))
            nombre_est = str(est_dict.get("nombre", f"Estación {id_est}"))

            if not (0.0 <= x_est <= 1000.0 and 0.0 <= y_est <= 1000.0):
                raise ValueError(f"Las coordenadas de la estación {id_est} están fuera del rango [0.0, 1000.0].")

            zona_est = next((z for z in zonas_escenario if z.contiene_punto(x_est, y_est)), None)

            estacion_obj = Estacion(
                id_estacion=id_est,
                nombre=nombre_est,
                x=x_est,
                y=y_est,
                zona=zona_est,
            )

            if escenario and hasattr(escenario, "estaciones"):
                if isinstance(escenario.estaciones, list):
                    escenario.estaciones.append(estacion_obj)
                elif isinstance(escenario.estaciones, dict):
                    escenario.estaciones[id_est] = estacion_obj

        # 4. Asignar fecha e instanciar Evento
        fecha_hora_iso = str(d.get("fecha_hora", ""))

        evento = Evento(
            id_evento=id_evento,
            magnitud=float(d["magnitud"]),
            profundidad=float(d["profundidad"]),
            epicentro=epicentro,
            estacion_origen=estacion_obj,
            fecha_hora=fecha_hora_iso,
            estado=d.get("estado", "Pendiente"),
            estado_catalogo=d.get("estado_catalogo", "Activo"),
            id_referencia=d.get("id_referencia"),
            revision=int(d["revision"]),
        )

        if "estaciones" in d and isinstance(d["estaciones"], list):
            evento.estaciones = d["estaciones"]

        return evento

    @classmethod
    def evento_a_dict(cls, evento: Evento) -> Dict[str, Any]:
        """Convierte una instancia de Evento a un diccionario serializable para JSON."""
        # Extraer datos del epicentro
        x_epi = round(float(evento.epicentro.x), 1) if hasattr(evento, "epicentro") and evento.epicentro else 0.0
        y_epi = round(float(evento.epicentro.y), 1) if hasattr(evento, "epicentro") and evento.epicentro else 0.0

        zona_dict = None
        if hasattr(evento.epicentro, "zona") and evento.epicentro.zona:
            z = evento.epicentro.zona
            zona_dict = {
                "nombre": getattr(z, "nombre", "Zona Defecto"),
                "x_min": getattr(z, "x_min", 0.0),
                "x_max": getattr(z, "x_max", 1000.0),
                "y_min": getattr(z, "y_min", 0.0),
                "y_max": getattr(z, "y_max", 1000.0),
                "poblada": getattr(z, "poblada", False),
            }

        # Extraer datos de la estación origen
        est_origen_id = "EST-01"
        est_origen_datos = None

        if hasattr(evento, "estacion_origen") and evento.estacion_origen:
            if isinstance(evento.estacion_origen, Estacion):
                est_origen_id = evento.estacion_origen.id_estacion
                est_origen_datos = {
                    "nombre": evento.estacion_origen.nombre,
                    "x": round(float(evento.estacion_origen.x), 1),
                    "y": round(float(evento.estacion_origen.y), 1),
                }
            else:
                est_origen_id = str(evento.estacion_origen)

        return {
            "id": int(evento.id),
            "magnitud": round(float(evento.magnitud), 1),
            "profundidad": round(float(evento.profundidad), 1),
            "epicentro": {
                "x": x_epi,
                "y": y_epi,
                "zona": zona_dict
            },
            "estacion_origen": est_origen_id,
            "estacion_origen_datos": est_origen_datos,
            "fecha_hora": str(evento.fecha_hora),
            "revision": int(evento.revision),
            "estado": str(evento.estado),
            "estado_catalogo": getattr(evento, "estado_catalogo", "Activo"),
            "id_referencia": getattr(evento, "id_referencia", None),
            "estaciones": getattr(evento, "estaciones", [est_origen_id])
        }

    # =========================================================================
    # MÉTODOS DE CARGA (READ)
    # =========================================================================

    @classmethod
    def cargar_eventos_json(cls, ruta_archivo: str, escenario: Any = None) -> List[Evento]:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            datos = json.load(f)

        if not isinstance(datos, list):
            raise ValueError("El archivo JSON debe contener una lista de eventos.")

        eventos = []
        for i, item in enumerate(datos):
            try:
                ev = cls.dict_a_evento(item, escenario)
                eventos.append(ev)
            except ValueError as ve:
                raise ValueError(f"Error en el evento #{i + 1} (ID: {item.get('id', 'N/A')}): {ve}")

        return eventos

    @classmethod
    def cargar_por_inserciones(cls, *args, **kwargs) -> bool:
        ruta_archivo, escenario, parent = cls._extraer_argumentos(args, kwargs)

        if not ruta_archivo:
            ruta_archivo = filedialog.askopenfilename(
                title="Seleccionar JSON de Inserciones",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                parent=parent,
            )

        if not ruta_archivo:
            return False

        try:
            eventos = cls.cargar_eventos_json(ruta_archivo, escenario)

            for ev in eventos:
                if escenario and hasattr(escenario, "dict_eventos"):
                    if ev.id in escenario.dict_eventos:
                        raise ValueError(f"El ID {ev.id} ya existe en el escenario y no se puede duplicar.")
                    escenario.dict_eventos[ev.id] = ev

                if escenario and hasattr(escenario, "arbol_avl") and escenario.arbol_avl:
                    nodo = Nodo(ev)
                    escenario.arbol_avl.insertar(nodo, escenario.L)

            return True

        except Exception as error:
            print(f"Error al cargar por inserciones: {error}")
            messagebox.showerror(
                "Error de Validación JSON",
                f"No se pudo cargar el archivo por violar las reglas de negocio:\n\n{error}",
                parent=parent,
            )
            return False

    @classmethod
    def cargar_por_topologia(cls, *args, **kwargs) -> bool:
        ruta_archivo, escenario, parent = cls._extraer_argumentos(args, kwargs)

        if not ruta_archivo:
            ruta_archivo = filedialog.askopenfilename(
                title="Seleccionar JSON de Topología",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                parent=parent,
            )

        if not ruta_archivo:
            return False

        try:
            eventos = cls.cargar_eventos_json(ruta_archivo, escenario)

            for ev in eventos:
                if escenario and hasattr(escenario, "dict_eventos"):
                    if ev.id in escenario.dict_eventos:
                        ev_existente = escenario.dict_eventos[ev.id]

                        p_ant = ev_existente.prioridad
                        m_ant = ev_existente.magnitud

                        ev_existente.magnitud = ev.magnitud
                        ev_existente.profundidad = ev.profundidad
                        ev_existente.epicentro = ev.epicentro
                        ev_existente.fecha_hora = ev.fecha_hora
                        ev_existente.revision = ev.revision

                        ev_existente.calcular_prioridad()

                        if hasattr(escenario, "arbol_avl") and escenario.arbol_avl:
                            escenario.arbol_avl.eliminar((p_ant, m_ant, ev.id), escenario.L)
                            nodo = Nodo(ev_existente)
                            escenario.arbol_avl.insertar(nodo, escenario.L)
                    else:
                        escenario.dict_eventos[ev.id] = ev
                        if hasattr(escenario, "arbol_avl") and escenario.arbol_avl:
                            nodo = Nodo(ev)
                            escenario.arbol_avl.insertar(nodo, escenario.L)

            return True

        except Exception as error:
            print(f"Error al cargar topología: {error}")
            messagebox.showerror(
                "Error de Carga de Topología",
                f"Error en el formato de los datos:\n\n{error}",
                parent=parent,
            )
            return False

    # =========================================================================
    # MÉTODOS DE GUARDADO (WRITE)
    # =========================================================================

    @classmethod
    def guardar_secuencia_inserciones(cls, *args, **kwargs) -> bool:
        """Guarda los eventos del escenario actual en un archivo JSON."""
        ruta_archivo, escenario, parent = cls._extraer_argumentos(args, kwargs)

        if not escenario or not hasattr(escenario, "dict_eventos"):
            messagebox.showwarning("Advertencia", "No hay eventos en el escenario para guardar.", parent=parent)
            return False

        if not ruta_archivo:
            ruta_archivo = filedialog.asksaveasfilename(
                title="Guardar Secuencia de Inserciones",
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
                parent=parent,
            )

        if not ruta_archivo:
            return False

        try:
            lista_eventos = list(escenario.dict_eventos.values())
            datos_json = [cls.evento_a_dict(ev) for ev in lista_eventos]

            with open(ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(datos_json, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Éxito", f"Se guardaron {len(datos_json)} eventos correctamente.", parent=parent)
            return True

        except Exception as error:
            print(f"Error al guardar inserciones: {error}")
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el archivo:\n{error}", parent=parent)
            return False

    @classmethod
    def guardar_escenario_completo(cls, *args, **kwargs) -> bool:
        """Alias para guardar todo el estado del escenario actual en JSON."""
        return cls.guardar_secuencia_inserciones(*args, **kwargs)

    # =========================================================================
    # AUXILIARES
    # =========================================================================

    @staticmethod
    def _extraer_argumentos(args, kwargs) -> tuple:
        ruta_archivo = None
        escenario = None
        parent = kwargs.get("parent_window") or kwargs.get("parent")

        for arg in args:
            if isinstance(arg, str):
                ruta_archivo = arg
            elif (
                hasattr(arg, "dict_eventos")
                or hasattr(arg, "arbol_avl")
                or hasattr(arg, "zonas")
                or hasattr(arg, "estaciones")
            ):
                escenario = arg

        if not escenario and "escenario" in kwargs:
            escenario = kwargs["escenario"]

        return ruta_archivo, escenario, parent


