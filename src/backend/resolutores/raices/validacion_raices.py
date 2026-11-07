"""Validación común de expresión, extremos finitos y límites de iteración."""
import math

from .limites_raices import (
    LIMITE_ITERACIONES_DEFECTO,
    LIMITE_ITERACIONES_MAXIMO,
    LONGITUD_MAXIMA_EXPRESION,
)


def validar_expresion(valor) -> str:
    """Devuelve la expresión recortada o lanza ValueError si es vacía o excede el límite."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("La expresión f(x) es obligatoria y no puede estar vacía.")
    if len(valor) > LONGITUD_MAXIMA_EXPRESION:
        raise ValueError(f"La expresión excede {LONGITUD_MAXIMA_EXPRESION} caracteres.")
    return valor.strip()


def validar_extremo(valor, nombre: str) -> float:
    """Devuelve el extremo finito como float o lanza ValueError con el nombre del campo."""
    if isinstance(valor, bool):
        raise ValueError(f"El extremo {nombre} no puede ser booleano.")
    if not isinstance(valor, (int, float)):
        raise ValueError(f"El extremo {nombre} debe ser numérico (recibido {valor!r}).")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ValueError(f"El extremo {nombre} excede la capacidad numérica.") from error
    if not math.isfinite(numero):
        raise ValueError(f"El extremo {nombre} debe ser finito (recibido {valor!r}).")
    return numero


def validar_limite_iteraciones(valor) -> int:
    """Devuelve el límite entero o el predeterminado si es None; lanza ValueError fuera de rango."""
    if valor is None:
        return LIMITE_ITERACIONES_DEFECTO
    if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= LIMITE_ITERACIONES_MAXIMO:
        raise ValueError(
            f"El límite de iteraciones debe ser un entero entre 1 y {LIMITE_ITERACIONES_MAXIMO} (recibido {valor!r})."
        )
    return valor