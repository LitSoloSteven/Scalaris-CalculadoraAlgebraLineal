"""Calculos matriciales puros reutilizables por servicios y trazas didacticas."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from src.backend.utilidades.validadores import validar_dimensiones_multiplicacion, validar_mismas_dimensiones


def operar_celda(izquierda, derecha, simbolo: str):
    """Devuelve suma o resta de los valores recibidos segun simbolo."""
    return izquierda + derecha if simbolo == "+" else izquierda - derecha


def producto_celda(izquierda: Matriz, derecha: Matriz, fila: int, columna: int):
    """Devuelve el producto punto de fila de izquierda por columna de derecha."""
    return sum((izquierda.obtener(fila, indice) * derecha.obtener(indice, columna)
                for indice in range(izquierda.columnas)), start=Fraction(0))


def restar_matrices(izquierda: Matriz, derecha: Matriz) -> Matriz:
    """Devuelve izquierda menos derecha; lanza ValueError si sus formas difieren."""
    validar_mismas_dimensiones(izquierda, derecha)
    datos = [[operar_celda(izquierda.obtener(fila, columna), derecha.obtener(fila, columna), "-")
              for columna in range(izquierda.columnas)] for fila in range(izquierda.filas)]
    return Matriz(izquierda.filas, izquierda.columnas, datos)


def multiplicar_matrices(izquierda: Matriz, derecha: Matriz) -> Matriz:
    """Devuelve izquierda por derecha; lanza ValueError si sus dimensiones son incompatibles."""
    validar_dimensiones_multiplicacion(izquierda, derecha)
    datos = [[producto_celda(izquierda, derecha, fila, columna) for columna in range(derecha.columnas)]
             for fila in range(izquierda.filas)]
    return Matriz(izquierda.filas, derecha.columnas, datos)


def es_identidad(matriz: Matriz | None, dimension: int) -> bool:
    """Devuelve si matriz coincide exactamente con la identidad de dimension; un producto ausente no coincide."""
    return matriz.datos == identidad(dimension).datos if matriz else False
