"""Conversión exacta de una celda con ubicación y política de vacío explícitas."""
from fractions import Fraction
from src.backend.utilidades.validadores import ValidadorMatriz


def parsear_celda_exacta(valor: object, coordenada: str, vacio_como_cero: bool = False) -> Fraction:
    """Convierte una celda; lanza ValueError con su coordenada si el validador la rechaza."""
    texto = str(valor).strip() if valor is not None else "0"
    if vacio_como_cero and not texto:
        texto = "0"
    valida, numero, error = ValidadorMatriz.parsear_numero_exacto(texto)
    if not valida:
        raise ValueError(f"{coordenada}: {error}")
    return numero
