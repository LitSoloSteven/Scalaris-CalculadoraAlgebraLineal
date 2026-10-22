"""Construcciones matriciales comunes sin trazas ni formato de presentacion."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz


def identidad(dimension: int) -> Matriz:
    """Devuelve la identidad de dimension; Matriz valida el orden y puede lanzar ValueError."""
    return Matriz(dimension, dimension, [[Fraction(fila == columna) for columna in range(dimension)]
                                       for fila in range(dimension)])


def transpuesta(matriz: Matriz) -> Matriz:
    """Devuelve una nueva Matriz con filas y columnas de matriz intercambiadas."""
    datos = [[matriz.obtener(fila, columna) for fila in range(matriz.filas)]
             for columna in range(matriz.columnas)]
    return Matriz(matriz.columnas, matriz.filas, datos)


def aumentar_con_identidad(matriz: Matriz) -> Matriz:
    """Devuelve el bloque aumentado de matriz e identidad de su numero de filas."""
    bloque = identidad(matriz.filas)
    return Matriz(matriz.filas, matriz.columnas + matriz.filas,
                  [fila + identidad_fila for fila, identidad_fila in zip(matriz.datos, bloque.datos)])


def matriz_de_columnas(vectores: list[Matriz]) -> Matriz:
    """Devuelve una matriz con los vectores columna compatibles y no vacios recibidos."""
    return Matriz(vectores[0].filas, len(vectores),
                  [[vector.obtener(fila, 0) for vector in vectores] for fila in range(vectores[0].filas)])
