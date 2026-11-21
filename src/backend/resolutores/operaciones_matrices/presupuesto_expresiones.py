"""Presupuestos de captura y trazabilidad para expresiones matriciales."""
from fractions import Fraction

from src.backend.constantes import (
    LONGITUD_MAXIMA_EXPRESION_MATRICIAL,
    MAXIMO_CELDAS_TRAZADAS_EXPRESION,
    MAXIMO_OPERACIONES_EXPRESION_MATRICIAL,
)
from src.backend.modelos.matriz import Matriz
from .analizador_expresiones import OPERADORES_BINARIOS, exponente_de

_MAXIMO_BITS_EXPRESION = 8192
_MENSAJE_DIMENSIONES = (
    "La expresión genera demasiados pasos para esas dimensiones. "
    "Reduce las dimensiones o divide la expresión."
)


def validar_longitud_expresion(expresion: str) -> None:
    """Rechaza con ValueError entradas demasiado largas antes del análisis léxico."""
    if len(expresion) > LONGITUD_MAXIMA_EXPRESION_MATRICIAL:
        raise ValueError(
            f"La expresión supera {LONGITUD_MAXIMA_EXPRESION_MATRICIAL} caracteres. "
            "Divídela en expresiones más cortas."
        )


def validar_presupuesto_operaciones(tokens: list[str], matrices: dict) -> None:
    """Rechaza con ValueError trabajo excesivo antes de calcular o guardar pasos."""
    operaciones = sum(_costo_operacion(token) for token in tokens)
    if operaciones > MAXIMO_OPERACIONES_EXPRESION_MATRICIAL:
        raise ValueError(
            f"La expresión supera {MAXIMO_OPERACIONES_EXPRESION_MATRICIAL} operaciones. "
            "Divídela en expresiones más cortas."
        )
    matrices_usadas = [matrices[token] for token in tokens if token in matrices]
    dimension = max((max(matriz.filas, matriz.columnas) for matriz in matrices_usadas), default=1)
    # Cada celda calculada puede conservar una instantánea completa del resultado.
    celdas_trazadas = operaciones * dimension ** 4
    if celdas_trazadas > MAXIMO_CELDAS_TRAZADAS_EXPRESION:
        raise ValueError(_MENSAJE_DIMENSIONES)


def _costo_operacion(token: str) -> int:
    exponente = exponente_de(token)
    if exponente is not None:
        return max(1, abs(exponente))
    return int(token in OPERADORES_BINARIOS or token in ("ᵀ", "¬"))


class PresupuestoExpresion:
    """Acumula el costo de las formas intermedias antes de reservar sus matrices."""

    def __init__(self) -> None:
        """Inicializa el presupuesto restante de una evaluación."""
        self._disponible = MAXIMO_CELDAS_TRAZADAS_EXPRESION

    def reservar(self, filas: int, columnas: int, operaciones: int = 1) -> None:
        """Descuenta el costo de las instantáneas o lanza ValueError si excede la cota."""
        self._disponible -= (filas * columnas) ** 2 * operaciones
        if self._disponible < 0:
            raise ValueError(_MENSAJE_DIMENSIONES)


def validar_magnitud(valor: Fraction | Matriz, factor: int = 1) -> None:
    """Rechaza racionales que excederían la cota de bits con el factor de crecimiento indicado."""
    valores = (celda for fila in valor.datos for celda in fila) if isinstance(valor, Matriz) else (valor,)
    for celda in valores:
        if isinstance(celda, (Fraction, int)):
            bits = max(celda.numerator.bit_length(), celda.denominator.bit_length())
            if bits * factor > _MAXIMO_BITS_EXPRESION:
                raise ValueError("La expresión genera números demasiado grandes. Usa valores o potencias menores.")
