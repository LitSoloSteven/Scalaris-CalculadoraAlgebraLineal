"""Determinante exacto mediante la reduccion comun, sin presentacion."""
from fractions import Fraction
from math import prod
from collections.abc import Callable

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas


def triangular_y_determinante(matriz: Matriz, registrar: Callable | None = None,
                             estrategia: str = "primer_no_nulo") -> tuple[Fraction, dict]:
    """Devuelve determinante y reduccion cuadrada con observador; lanza ValueError si la estrategia bloquea el pivote."""
    dimension = matriz.filas
    copia = Matriz(dimension, dimension, [[Fraction(valor) for valor in fila] for fila in matriz.datos])
    opciones = ConfiguracionReduccion(estrategia_pivote=estrategia, normalizar_pivotes=False)
    reduccion = ReductorFilas(copia, dimension, opciones, registrar).reducir()
    if reduccion["pivote_bloqueado"] is not None:
        raise ValueError("El determinante requiere intercambiar filas; selecciona pivoteo parcial.")
    if reduccion["rango"] < dimension:
        return Fraction(0), reduccion
    triangular = reduccion["matriz_reducida"]
    signo = (-1) ** reduccion["intercambios"]
    return signo * prod((triangular.obtener(i, i) for i in range(dimension)), start=Fraction(1)), reduccion
