"""Datos opcionales del resultado de una inversa fallida o singular."""
from fractions import Fraction
from typing import TypedDict
from src.backend.modelos.matriz import Matriz


class OpcionesResultadoVacio(TypedDict, total=False):
    """Describe los datos ya calculados que acompañan el error de la inversa."""

    dimension: int
    tiempo_s: float
    determinante: Fraction | None
    matriz_a: Matriz | None
    celda_error: list[int] | None
