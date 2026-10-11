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
