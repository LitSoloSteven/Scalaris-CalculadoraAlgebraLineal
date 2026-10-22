"""Conversion de entradas escalares y limites comunes sin dependencias matriciales."""
from fractions import Fraction
from typing import Any

from src.backend.constantes import (
    LIMITE_RECONSTRUCCION_ESTRICTA, LONGITUD_MAXIMA_CADENA_NUMERO,
    MENSAJE_NOTACION_CIENTIFICA_NO_SOPORTADA, MENSAJE_NUMERO_DEMASIADO_LARGO,
)


def motivo_cadena_no_soportada(texto: str) -> str | None:
    """Devuelve el rechazo de notacion o longitud de texto, o None si esta admitido."""
    if "e" in texto or "E" in texto:
        return MENSAJE_NOTACION_CIENTIFICA_NO_SOPORTADA
    if len(texto) > LONGITUD_MAXIMA_CADENA_NUMERO:
        return MENSAJE_NUMERO_DEMASIADO_LARGO
    return None


def _convertir_flotante(valor: float) -> tuple[bool, Fraction, str]:
    try:
        return True, Fraction(valor).limit_denominator(LIMITE_RECONSTRUCCION_ESTRICTA), ""
    except (ValueError, OverflowError):
        try:
            return True, Fraction(str(valor)), ""
        except (ValueError, ZeroDivisionError):
            return False, Fraction(0), "Valor flotante no convertible a fracción."


def _convertir_texto(valor: str) -> tuple[bool, Fraction, str]:
    texto = valor.strip()
    if not texto:
        return False, Fraction(0), "El campo está vacío."
    rechazo = motivo_cadena_no_soportada(texto)
    if rechazo is not None:
        return False, Fraction(0), rechazo
    try:
        return True, Fraction(texto), ""
    except ZeroDivisionError:
        return False, Fraction(0), "División por cero en la fracción ingresada."
    except ValueError:
        return False, Fraction(0), "El valor ingresado no es un número o fracción válida."


def convertir_numero_exacto(valor: Any) -> tuple[bool, Fraction, str]:
    """Devuelve validez, fraccion y mensaje de valor; conserva la politica historica para flotantes."""
    if isinstance(valor, (int, Fraction)):
        return True, Fraction(valor), ""
    if isinstance(valor, float):
        return _convertir_flotante(valor)
    if isinstance(valor, str):
        return _convertir_texto(valor)
    return False, Fraction(0), f"Tipo no soportado: {type(valor).__name__}"
