"""Sustituciones exactas para sistemas triangulares de una factorizacion LU."""
from fractions import Fraction
from typing import TypedDict

from src.backend.modelos.matriz import Matriz


class DatosFilaSustitucion(TypedDict):
    """Datos exactos de una fila, su acumulado y el valor despejado."""

    fila: int
    termino: Fraction
    productos: list[Fraction]
    acumulado: Fraction
    diagonal: Fraction
    valor: Fraction


def sustituir_adelante(inferior: Matriz, terminos: list[Fraction]) -> tuple[list[Fraction], list[DatosFilaSustitucion]]:
    """Resuelve Ly=terminos para L unitaria y devuelve valores y operaciones por fila.

    Recibe la matriz inferior y el vector de terminos; presupone dimensiones compatibles.
    """
    valores: list[Fraction] = []
    filas: list[DatosFilaSustitucion] = []
    for fila in range(inferior.filas):
        productos = [Fraction(inferior.obtener(fila, columna)) * valores[columna] for columna in range(fila)]
        acumulado = sum(productos, Fraction(0))
        valor = Fraction(terminos[fila]) - acumulado
        valores.append(valor)
        filas.append({"fila": fila, "termino": Fraction(terminos[fila]), "productos": productos,
                      "acumulado": acumulado, "diagonal": Fraction(1), "valor": valor})
    return valores, filas


def sustituir_atras(superior: Matriz, terminos: list[Fraction]) -> tuple[list[Fraction], list[DatosFilaSustitucion]]:
    """Resuelve Ux=terminos y devuelve valores y operaciones por fila descendente.

    Recibe la matriz superior y el vector de terminos; presupone dimensiones compatibles.
    Lanza ZeroDivisionError si una entrada diagonal es cero.
    """
    valores = [Fraction(0) for _ in terminos]
    filas: list[DatosFilaSustitucion] = []
    for fila in range(superior.filas - 1, -1, -1):
        productos = [Fraction(superior.obtener(fila, columna)) * valores[columna]
                     for columna in range(fila + 1, superior.columnas)]
        acumulado = sum(productos, Fraction(0))
        diagonal = Fraction(superior.obtener(fila, fila))
        valor = (Fraction(terminos[fila]) - acumulado) / diagonal
        valores[fila] = valor
        filas.append({"fila": fila, "termino": Fraction(terminos[fila]), "productos": productos,
                      "acumulado": acumulado, "diagonal": diagonal, "valor": valor})
    return valores, filas
