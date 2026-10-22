"""Construcción exacta de la cadena acumulada de una combinación lineal."""
from dataclasses import dataclass
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.utilidades.validadores import ValidadorMatriz


@dataclass(frozen=True)
class PasoCadena:
    """Coordenadas exactas y etiqueta pedagógica de una suma parcial."""

    coordenadas: tuple[Fraction, ...]
    etiqueta: str


def _extraer_coeficientes_exactos(resultado: dict) -> list:
    coeficientes = resultado.get("coeficientes") or []
    if coeficientes:
        return coeficientes
    coeficientes = []
    for texto in resultado.get("coeficientes_texto", []):
        valido, valor, _ = ValidadorMatriz.parsear_numero_exacto(texto)
        coeficientes.append(valor if valido else Fraction(0))
    return coeficientes


def calcular_cadena_acumulada(
    resultado: dict, columnas: list[Matriz], dimension: int,
) -> list[PasoCadena]:
    """Devuelve pasos de sumas exactas en orden usando coeficientes o coeficientes_texto y columnas de la dimensión recibida.
    Lanza IndexError si faltan columnas o filas; ValueError, TypeError o ZeroDivisionError si un coeficiente no admite Fraction."""
    cadena = []
    acumulado = [Fraction(0)] * dimension
    for indice, coeficiente in enumerate(_extraer_coeficientes_exactos(resultado)):
        coeficiente = Fraction(coeficiente)
        for componente in range(dimension):
            acumulado[componente] += coeficiente * Fraction(columnas[indice].obtener(componente, 0))
        etiqueta = f"c_{indice+1}·v_{indice+1}" if indice == 0 else f"+ c_{indice+1}·v_{indice+1}"
        cadena.append(PasoCadena(tuple(acumulado), etiqueta))
    return cadena
