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

DESTINOS_MATRIZ_RECTANGULAR = frozenset({"factorizacion_lu", "sistemas", "matrices", "transformaciones"})


def _admite_dimensiones(destino: str, filas: int, columnas: int) -> bool:
    minimo, maximo = LIMITES_DESTINOS_MATRIZ[destino]
    return (minimo <= filas <= maximo and minimo <= columnas <= maximo
            and (filas == columnas or destino in DESTINOS_MATRIZ_RECTANGULAR))


def destinos_compatibles(filas: int, columnas: int, origen: str) -> tuple[str, ...]:
    """Devuelve destinos que admiten ambos ejes y la forma, excluyendo el origen;
    devuelve una tupla vacía para vectores o dimensiones inválidas."""
    if type(filas) is not int or type(columnas) is not int:
        return ()
    if origen == "vectores":
        return ()
    return tuple(destino for destino in LIMITES_DESTINOS_MATRIZ
                 if destino != origen and _admite_dimensiones(destino, filas, columnas))
