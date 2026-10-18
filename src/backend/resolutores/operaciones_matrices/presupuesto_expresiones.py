"""Presupuestos de captura y trazabilidad para expresiones matriciales."""
from src.backend.constantes import (
    LONGITUD_MAXIMA_EXPRESION_MATRICIAL,
    MAXIMO_CELDAS_TRAZADAS_EXPRESION,
    MAXIMO_OPERACIONES_EXPRESION_MATRICIAL,
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
    operaciones = sum(token in {"+", "-", "*", "ᵀ", "¬"} for token in tokens)
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
        raise ValueError(
            "La expresión genera demasiados pasos para esas dimensiones. "
            "Reduce las dimensiones o divide la expresión."
        )
