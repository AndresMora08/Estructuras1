from datetime import datetime


def obtener_eventos_escenario(escenario):
    """
    Obtiene los eventos del escenario, independientemente
    de si están almacenados en un diccionario, lista o árbol AVL.
    """
    if not escenario:
        return []

    # 1. Diccionario principal de eventos
    dict_eventos = getattr(escenario, "dict_eventos", None)
    if dict_eventos:
        return list(dict_eventos.values())

    # 2. Árbol AVL utilizado por la interfaz
    arbol_avl = getattr(escenario, "arbol_avl", None)
    if arbol_avl:
        if hasattr(arbol_avl, "obtener_todos_los_eventos"):
            return arbol_avl.obtener_todos_los_eventos()
        if hasattr(arbol_avl, "inorden"):
            return arbol_avl.inorden()

    # 3. Árbol de eventos alternativo
    arbol_eventos = getattr(escenario, "arbol_eventos", None)
    if arbol_eventos:
        if hasattr(arbol_eventos, "obtener_todos_los_eventos"):
            return arbol_eventos.obtener_todos_los_eventos()
        if hasattr(arbol_eventos, "inorden"):
            return arbol_eventos.inorden()

    # 4. Lista de eventos
    eventos = getattr(escenario, "eventos", None)
    if eventos is not None:
        return list(eventos)

    return []


def obtener_fecha(evento):
    """
    Obtiene la fecha del evento como datetime.
    """
    fecha = getattr(evento, "fecha", None)
    if isinstance(fecha, datetime):
        return fecha

    fecha_hora = getattr(evento, "fecha_hora", None)
    if isinstance(fecha_hora, datetime):
        return fecha_hora

    if fecha_hora:
        try:
            return datetime.fromisoformat(
                fecha_hora.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            pass

    raise ValueError(
        f"El evento {getattr(evento, 'id', '?')} "
        "no tiene una fecha válida."
    )


def normalizar_fecha(fecha):
    """
    Normaliza las fechas a UTC sin zona horaria para
    permitir comparaciones entre fechas ISO y datetime.
    """
    if fecha.tzinfo is not None:
        fecha = fecha.astimezone(
            datetime.now().astimezone().tzinfo
        )
        fecha = fecha.replace(tzinfo=None)
    return fecha


def es_candidato(evento_A, evento_B, W, R):
    """
    Evalúa si evento_A puede ser el evento principal
    de evento_B.
    """
    estado_A = getattr(evento_A, "estado", "")
    estado_B = getattr(evento_B, "estado", "")

    if hasattr(estado_A, "value"):
        estado_A = estado_A.value
    if hasattr(estado_B, "value"):
        estado_B = estado_B.value

    if str(estado_A).upper() == "ELIMINADO":
        return False
    if str(estado_B).upper() == "ELIMINADO":
        return False

    # 1. Magnitud estrictamente mayor
    if evento_A.magnitud <= evento_B.magnitud:
        return False

    # 2. Comparación de fechas
    fecha_A = normalizar_fecha(obtener_fecha(evento_A))
    fecha_B = normalizar_fecha(obtener_fecha(evento_B))

    if fecha_A >= fecha_B:
        return False

    # 3. Ventana temporal
    diferencia_horas = (
        fecha_B - fecha_A
    ).total_seconds() / 3600.0

    if diferencia_horas > W or diferencia_horas < 0:
        return False

    # 4. Distancia entre epicentros
    dx = evento_A.epicentro.x - evento_B.epicentro.x
    dy = evento_A.epicentro.y - evento_B.epicentro.y

    distancia_cuadrado = dx * dx + dy * dy

    if distancia_cuadrado > R * R:
        return False

    return True


def seleccionar_referencia(evento_B, candidatos):
    """
    Selecciona el evento principal aplicando:
    1. Mayor magnitud.
    2. Menor distancia.
    3. Fecha más antigua.
    4. Menor ID.
    """
    if not candidatos:
        return None

    def clave_desempate(candidato):
        dx = (
            candidato.epicentro.x
            - evento_B.epicentro.x
        )
        dy = (
            candidato.epicentro.y
            - evento_B.epicentro.y
        )
        distancia_cuadrado = dx * dx + dy * dy

        try:
            id_key = (0, int(candidato.id))
        except (ValueError, TypeError):
            id_key = (1, str(candidato.id))

        fecha = normalizar_fecha(
            obtener_fecha(candidato)
        )

        return (
            -candidato.magnitud,
            distancia_cuadrado,
            fecha,
            id_key
        )

    elegido = min(
        candidatos,
        key=clave_desempate
    )

    return elegido.id


def recalcular_asociaciones_escenario(escenario, W, R):
    """
    Recalcula las asociaciones sísmicas de todos
    los eventos del escenario activo.
    """
    if not escenario:
        return

    if W <= 0 or R <= 0:
        raise ValueError(
            "W y R deben ser mayores que cero."
        )

    # Obtener todos los eventos
    todos = obtener_eventos_escenario(escenario)

    if not todos:
        return

    # 1. Limpiar referencias anteriores
    for evento in todos:
        evento.id_referencia = None
        evento.candidatos_ids = []

    # 2. Excluir eventos eliminados
    eventos_validos = []
    for evento in todos:
        estado = getattr(evento, "estado", "")
        if hasattr(estado, "value"):
            estado = estado.value

        if str(estado).upper() != "ELIMINADO":
            eventos_validos.append(evento)

    # 3. Buscar referencia para cada evento
    for evento_B in eventos_validos:
        candidatos = [
            evento_A
            for evento_A in eventos_validos
            if (
                evento_A.id != evento_B.id
                and es_candidato(
                    evento_A,
                    evento_B,
                    W,
                    R
                )
            )
        ]

        evento_B.id_referencia = seleccionar_referencia(
            evento_B,
            candidatos
        )
        
        # Guardamos la lista de IDs de los candidatos encontrados
        evento_B.candidatos_ids = [c.id for c in candidatos]

    return todos