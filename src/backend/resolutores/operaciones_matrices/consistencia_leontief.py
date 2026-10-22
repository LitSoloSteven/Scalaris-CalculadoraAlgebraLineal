"""Clasificación exacta del balance de Leontief cuando no existe multiplicador."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss


def resolver_balance_singular(matriz: Matriz, demanda: list[Fraction]) -> dict:
    """Resuelve matriz por producción igual a demanda con Gauss exacto y devuelve su contrato."""
    aumentada = Matriz(matriz.filas, matriz.columnas + 1,
                       [fila + [Fraction(valor)] for fila, valor in zip(matriz.datos, demanda)])
    return ResolutorGauss(aumentada, tolerancia_cero=0).resolver()
