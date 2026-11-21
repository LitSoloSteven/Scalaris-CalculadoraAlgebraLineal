"""Conversión léxica compartida; la validez matemática pertenece al dominio."""
import math
from decimal import Decimal, DecimalException

from src.backend.resolutores.raices.funcion_real.evaluacion.evaluador_funcion import evaluar_constante_real

def entero_capturado(valor: object, etiqueta: str) -> int:
    """Convierte un campo con su etiqueta a entero sin truncar; lanza ValueError."""
    try:
        numero = float(valor)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f"{etiqueta} debe ser un entero.") from error
    if isinstance(valor, bool) or not math.isfinite(numero) or not numero.is_integer():
        raise ValueError(f"{etiqueta} debe ser un entero.")
    if isinstance(valor, str):
        try:
            exacto = Decimal(valor.strip())
            if exacto != exacto.to_integral_value():
                raise ValueError(f"{etiqueta} debe ser un entero.")
            return int(exacto)
        except DecimalException as error:
            raise ValueError(f"{etiqueta} debe ser un entero representable.") from error
    return int(numero)


def real_capturado(valor: object, etiqueta: str) -> float:
    """Convierte un campo real o una expresión constante; lanza ValueError con su etiqueta."""
    try:
        if isinstance(valor, bool):
            raise ValueError
        return _texto_real(valor) if isinstance(valor, str) else float(valor)
    except (ValueError, TypeError, OverflowError, DecimalException) as error:
        raise ValueError(f"{etiqueta} debe ser un número real. Usa un punto para los decimales.") from error


def _texto_real(texto: str) -> float:
    try:
        numero = float(texto)
    except ValueError:
        return evaluar_constante_real(texto)
    if numero == 0 and Decimal(texto.strip()) != 0:
        return evaluar_constante_real(texto)
    return numero
