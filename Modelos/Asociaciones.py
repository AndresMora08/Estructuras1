import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

FORMATO_FECHA_ISO = "%Y-%m-%dT%H:%M:%SZ"
EPSILON = 1e-9


def obtener_eventos_escenario(escenario):
    """
    Events that take part in associations: active + archived.
    Removed (retired) events are never considered.
    """
    if not escenario:
        return []

    activos = getattr(escenario, "dict_eventos", None) or {}
    eventos = list(activos.values())
    ids = set(activos.keys())

    for evento in getattr(escenario, "historico", None) or []:
        if evento.estado_catalogo == "Archivado" and evento.id not in ids:
            eventos.append(evento)
            ids.add(evento.id)
    return eventos


def normalizar_fecha(fecha: datetime) -> datetime:
    """Returns an aware UTC datetime (naive values are assumed to be UTC)."""
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def obtener_fecha(evento) -> datetime:
    """Occurrence time of the event as an aware UTC datetime."""
    fecha_hora = getattr(evento, "fecha_hora", None)

    if isinstance(fecha_hora, datetime):
        return normalizar_fecha(fecha_hora)

    if isinstance(fecha_hora, str):
        try:
            return datetime.strptime(fecha_hora.strip(), FORMATO_FECHA_ISO).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
        try:
            return normalizar_fecha(datetime.fromisoformat(fecha_hora.strip().replace("Z", "+00:00")))
        except ValueError:
            pass

    raise ValueError(f"El evento {getattr(evento, 'id', '?')} no tiene una fecha válida.")


def distancia(evento_a, evento_b) -> float:
    """Euclidean distance between epicenters (km)."""
    return math.hypot(
        evento_a.epicentro.x - evento_b.epicentro.x,
        evento_a.epicentro.y - evento_b.epicentro.y,
    )


def es_candidato(evento_A, evento_B, W, R) -> bool:
    """
    A is a candidate reference of B when A has a strictly greater magnitude,
    occurred strictly before B, within at most W hours and at most R km.
    """
    if evento_A.magnitud <= evento_B.magnitud:
        return False

    fecha_A = obtener_fecha(evento_A)
    fecha_B = obtener_fecha(evento_B)
    if fecha_A >= fecha_B:
        return False

    diferencia_horas = (fecha_B - fecha_A).total_seconds() / 3600.0
    if diferencia_horas > W + EPSILON:
        return False

    return distancia(evento_A, evento_B) <= R + EPSILON


def seleccionar_referencia(evento_B, candidatos):
    """
    Deterministic choice that only depends on the data:
    1. Greater magnitude. 2. Smaller distance. 3. Older date. 4. Smaller id.
    Returns the id of the chosen event (or None).
    """
    if not candidatos:
        return None

    def clave_desempate(candidato):
        return (
            -candidato.magnitud,
            round(distancia(candidato, evento_B), 9),
            obtener_fecha(candidato),
            int(candidato.id),
        )

    return min(candidatos, key=clave_desempate).id


def recalcular_asociaciones_escenario(escenario, W, R):
    """Recomputes the associations of every active and archived event."""
    if not escenario:
        return

    if W <= 0 or R <= 0:
        raise ValueError("W y R deben ser mayores que cero.")

    validos = obtener_eventos_escenario(escenario)
    if not validos:
        return

    for evento in validos:
        evento.id_referencia = None
        evento.candidatos_ids = []

    for evento_B in validos:
        candidatos = [
            evento_A for evento_A in validos
            if evento_A.id != evento_B.id and es_candidato(evento_A, evento_B, W, R)
        ]
        evento_B.id_referencia = seleccionar_referencia(evento_B, candidatos)
        evento_B.candidatos_ids = sorted(c.id for c in candidatos)

    return validos


# ----------------------------------------------------------------------
# QUERY HELPERS
# ----------------------------------------------------------------------
def estado_en_catalogo(escenario, id_evento: int) -> Tuple[Optional[str], Optional[object]]:
    """Returns ('Activo' | 'Archivado' | 'Retirado' | None, event)."""
    if escenario is None:
        return None, None

    activo = (getattr(escenario, "dict_eventos", None) or {}).get(id_evento)
    if activo is not None:
        return "Activo", activo

    for evento in reversed(getattr(escenario, "historico", None) or []):
        if evento.id == id_evento:
            return evento.estado_catalogo, evento

    return None, None


def candidatos_de(escenario, evento_B, W=None, R=None) -> list:
    """Live candidates of B among active and archived events."""
    W = escenario.W if W is None else W
    R = escenario.R if R is None else R
    candidatos = [
        evento_A for evento_A in obtener_eventos_escenario(escenario)
        if evento_A.id != evento_B.id and es_candidato(evento_A, evento_B, W, R)
    ]
    return sorted(candidatos, key=lambda c: c.id)


def replicas_de(escenario, id_evento: int) -> list:
    """Events whose chosen reference is the given event."""
    return sorted(
        (e for e in obtener_eventos_escenario(escenario) if e.id_referencia == id_evento),
        key=lambda e: e.id,
    )


def auditar_referencias(escenario) -> List[str]:
    """
    Read-only check: references point to active/archived events (never removed
    or missing), there are no cycles, and no identity is duplicated between the
    active catalog and the history.
    """
    errores: List[str] = []
    activos = dict(getattr(escenario, "dict_eventos", None) or {})
    archivados: Dict[int, object] = {}
    retirados = set()
    vistos_historico = set()

    for evento in getattr(escenario, "historico", None) or []:
        if evento.id in vistos_historico:
            errores.append(f"SIS-{evento.id:06d}: identificador duplicado en el histórico.")
        vistos_historico.add(evento.id)
        if evento.id in activos:
            errores.append(f"SIS-{evento.id:06d}: está a la vez en eventos activos y en el histórico.")
        if evento.estado_catalogo == "Retirado":
            retirados.add(evento.id)
        elif evento.estado_catalogo == "Archivado":
            archivados[evento.id] = evento

    visibles = dict(archivados)
    visibles.update(activos)

    for id_evento, evento in visibles.items():
        referencia = evento.id_referencia
        if referencia is None:
            continue
        if referencia == id_evento:
            errores.append(f"SIS-{id_evento:06d}: se referencia a sí mismo.")
        elif referencia in retirados:
            errores.append(f"SIS-{id_evento:06d}: referencia al evento eliminado SIS-{referencia:06d}.")
        elif referencia not in visibles:
            errores.append(f"SIS-{id_evento:06d}: referencia a un evento inexistente SIS-{referencia:06d}.")

    reportados = set()
    for inicio in visibles:
        if inicio in reportados:
            continue
        camino: List[int] = []
        vistos = set()
        actual = inicio
        while actual is not None and actual in visibles and actual not in vistos:
            vistos.add(actual)
            camino.append(actual)
            actual = visibles[actual].id_referencia
        if actual is not None and actual in vistos:
            ciclo = camino[camino.index(actual):]
            errores.append("Ciclo de referencias: " + " -> ".join(f"SIS-{i:06d}" for i in ciclo + [actual]))
            reportados.update(ciclo)

    return errores