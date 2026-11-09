"""Conversión léxica compartida; la validez matemática pertenece al dominio."""
import math
from decimal import Decimal, DecimalException


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
    """Convierte campo y etiqueta a float sin bool; lanza ValueError si falla la conversión.
    El dominio valida después la finitud y los límites del número devuelto.
    """
    try:
        if isinstance(valor, bool):
            raise ValueError
        return float(valor)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(f"{etiqueta} debe ser un número real. Usa un punto para los decimales.") from error
