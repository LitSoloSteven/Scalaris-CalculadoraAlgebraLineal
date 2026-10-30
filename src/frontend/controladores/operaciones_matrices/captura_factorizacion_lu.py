"""Localización de celdas inválidas en una captura rectangular."""
from src.frontend.sugerencias import CeldaInvalida, primera_celda_invalida


def localizar_invalida(datos: list[list[str]]) -> CeldaInvalida | None:
    """Devuelve la primera celda inválida de los datos o None si no existe."""
    elementos = [(f"A[{fila + 1},{columna + 1}]", valor, (fila, columna))
                 for fila, valores in enumerate(datos) for columna, valor in enumerate(valores)]
    return primera_celda_invalida(elementos)
