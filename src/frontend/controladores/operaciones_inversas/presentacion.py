"""Preparacion de capacidades para presentar una matriz inversa."""
from src.backend.utilidades.estado_captura import opciones_dimension_inversa


def preparar_opciones_inversa(dimension: int) -> dict:
    """Delega al dominio las capacidades de captura, confirmacion y transferencia."""
    return opciones_dimension_inversa(dimension)
