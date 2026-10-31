"""Compatibilidad dimensional de las herramientas receptoras de matrices."""
from src.backend.constantes import (
    DIMENSION_MAXIMA_INVERSA, DIMENSION_MAXIMA_MATRICES, DIMENSION_MAXIMA_MODELOS,
    DIMENSION_MAXIMA_SISTEMAS, DIMENSION_MINIMA, DIMENSION_MINIMA_LEONTIEF,
)

LIMITES_DESTINOS_MATRIZ = {
    "inversa": (DIMENSION_MINIMA, DIMENSION_MAXIMA_INVERSA),
    "determinantes": (DIMENSION_MINIMA, DIMENSION_MAXIMA_INVERSA),
    "factorizacion_lu": (DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES),
    "sistemas": (DIMENSION_MINIMA, DIMENSION_MAXIMA_SISTEMAS),
    "matrices": (DIMENSION_MINIMA, DIMENSION_MAXIMA_MATRICES),
    "transformaciones": (DIMENSION_MINIMA, DIMENSION_MAXIMA_MODELOS),
    "leontief": (DIMENSION_MINIMA_LEONTIEF, DIMENSION_MAXIMA_MODELOS),
}


def destinos_compatibles(filas: int, columnas: int, origen: str) -> tuple[str, ...]:
    """Devuelve destinos cuadrados dentro de sus límites, excluyendo el origen;
    devuelve una tupla vacía para vectores y formas inválidas o rectangulares."""
    if type(filas) is not int or type(columnas) is not int:
        return ()
    if filas != columnas or origen == "vectores":
        return ()
    return tuple(destino for destino, (minimo, maximo) in LIMITES_DESTINOS_MATRIZ.items()
                 if destino != origen and minimo <= filas <= maximo)
