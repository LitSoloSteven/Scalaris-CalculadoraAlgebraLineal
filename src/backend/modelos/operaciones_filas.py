"""Operaciones elementales puras sobre filas numericas."""
from fractions import Fraction


def sumar_fila_multiplicada(destino: list, origen: list, factor: int | Fraction | float) -> list:
    """Devuelve destino mas factor por origen sin modificar las filas recibidas."""
    factor_exacto = type(factor) is Fraction
    return [valor_destino if factor_exacto and type(valor_destino) is Fraction
            and type(valor_origen) is Fraction and valor_origen == 0 else valor_destino + factor * valor_origen
            for valor_destino, valor_origen in zip(destino, origen)]
