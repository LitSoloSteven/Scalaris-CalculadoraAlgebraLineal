"""Signo del producto y acciones registradas por el motor de bisección."""
from typing import Literal

SignoProducto = Literal[-1, 0, 1]
AccionBiseccion = Literal["reemplazar_a", "reemplazar_b", "detener"]


def signo_producto(valor_izquierdo: float, valor_medio: float) -> SignoProducto:
    """Devuelve el signo del producto de dos evaluaciones finitas sin multiplicarlas."""
    if valor_izquierdo == 0 or valor_medio == 0:
        return 0
    return -1 if (valor_izquierdo < 0) != (valor_medio < 0) else 1
