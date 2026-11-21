"""Reconstrucción exacta de matrices producidas por los resolutores vectoriales."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz


def reconstruir_matriz_resultado(datos_matriz: dict) -> Matriz:
    """Reconstruye resultados serializados sin aplicarles límites de captura de entrada."""
    datos = [[Fraction(str(celda)) for celda in fila] for fila in datos_matriz["datos"]]
    return Matriz(datos_matriz["filas"], datos_matriz["columnas"], datos)
