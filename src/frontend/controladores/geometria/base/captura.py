"""Preparación de cargas de entrada para los controladores geométricos."""
from __future__ import annotations


def construir_carga_sistema(matriz: list, vector: list, vacia: bool) -> dict | None:
    """Devuelve A y b sin parsearlos, o ausencia de carga para una cuadrícula vacía."""
    if vacia or not matriz or not matriz[0]:
        return None
    return {"matriz_a": matriz, "vector_b": vector}


def construir_carga_vectores(escena: str, dimension: int, caches: list[dict]) -> dict | None:
    """Serializa las componentes capturadas manteniendo cero en entradas vacías."""
    if escena not in ('vectores', 'combinacion'):
        return None
    vectores = [
        {"datos": [cache.get(i, '0') or '0' for i in range(dimension)], "orientacion": "columna"}
        for cache in caches
    ]
    if not any(valor != '0' for vector in vectores for valor in vector["datos"]):
        return None
    if escena == 'vectores':
        return {"vectores": vectores}
    return {"objetivo": vectores[0], "vectores": vectores[1:]}
