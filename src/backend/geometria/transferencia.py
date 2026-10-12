"""Restricciones de escena para familias de vectores transferidas."""
from __future__ import annotations

LIMITES_VECTORES_ESCENA = {'vectores': (2, 2), 'combinacion': (2, 5)}


def validar_transferencia_escena(escena: str, escena_recibida: str, vectores: list) -> str | None:
    """Devuelve el motivo de rechazo por escena o cantidad, o None si cumple."""
    if escena_recibida != escena:
        return 'Los datos recibidos no son válidos, así que empezamos con la herramienta vacía.'
    minimo, maximo = LIMITES_VECTORES_ESCENA[escena]
    if minimo <= len(vectores) <= maximo:
        return None
    if escena == 'vectores':
        return 'La escena de Vectores requiere exactamente 2 vectores.'
    return 'La escena de Combinación lineal requiere entre 2 y 5 vectores (b + v1...v4).'


def _obtener_familia_escena(operacion: str, vectores: dict) -> tuple[list, str]:
    if operacion == "suma_resta":
        datos = [vector["data"] for vector in vectores.values()]
        escena = "vectores"
    elif operacion == "combinacion_lineal" and "b" in vectores:
        datos = [vectores["b"]["data"]] + [vector["data"] for nombre, vector in vectores.items() if nombre != "b"]
        escena = "combinacion"
    else:
        return [], ""
    return datos, escena


def preparar_vectores_visualizador(operacion: str, vectores: dict) -> tuple[list, str]:
    """Devuelve una familia compatible con las dimensiones y cantidades de la escena."""
    datos, escena = _obtener_familia_escena(operacion, vectores)
    if not escena:
        return [], ""
    minimo, maximo = LIMITES_VECTORES_ESCENA[escena]
    if not minimo <= len(datos) <= maximo:
        return [], ""
    dimension = len(datos[0])
    if dimension in (2, 3) and all(len(vector) == dimension for vector in datos):
        return datos, escena
    return [], ""
