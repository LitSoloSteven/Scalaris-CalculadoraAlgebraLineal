"""Definicion de tipos de solucion y validacion de invariantes parametricos."""

from fractions import Fraction
from typing import TypedDict


class ParametrosSolucion(TypedDict, total=False):
    """Representacion parametrica exacta del conjunto solucion de Ax = b."""

    numero_variables: int
    columnas_libres: list[int]
    nombres_parametros: list[str]
    particular: list[Fraction]
    direcciones: list[list[Fraction]]


def validar_invariantes_parametricos(
    direcciones: list[list[Fraction]],
    particular: list[Fraction],
    columnas_libres: list[int],
) -> None:
    """Verifica defensivamente las invariantes de construccion parametrica."""
    for k, columna_libre in enumerate(columnas_libres):
        assert direcciones[k][columna_libre] == 1, (
            f"Invariante rota: direcciones[{k}][{columna_libre}] debe ser 1."
        )
        assert particular[columna_libre] == 0, (
            f"Invariante rota: particular[{columna_libre}] debe ser 0."
        )
        for j, columna_libre_j in enumerate(columnas_libres):
            if j != k:
                assert direcciones[k][columna_libre_j] == 0, (
                    f"Invariante rota: direcciones[{k}][{columna_libre_j}] debe ser 0."
                )
