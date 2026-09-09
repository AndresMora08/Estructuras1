import json
from typing import Any, Dict


class CargadorJSON:

    @staticmethod
    def leer_archivo_json(ruta_archivo: str) -> Dict[str, Any]:

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"El archivo no existe en la ruta: {ruta_archivo}"
            )
        except json.JSONDecodeError as error:
            raise ValueError(f"El archivo no es un JSON válido: {error}")

        return {
            "reloj": datos.get("reloj"),
            "zonas": datos.get("zonas", []),
            "estaciones": datos.get("estaciones", []),
            "arbol": datos.get("arbol", {}),
            "cola_reportes": datos.get("cola_reportes", []),
            "historico": datos.get("historico", []),
        }