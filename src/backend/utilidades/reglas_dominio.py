"""Reglas de dominio y validaciones centralizadas del backend."""

from typing import Any
from src.backend.constantes import LONGITUD_MAXIMA_ENTRADA_BASES

BASES_NUMERICAS = {"decimal": 10, "binario": 2, "octal": 8, "hexadecimal": 16}


def _capturar_magnitud_base(limpio: str, base: int) -> int:
    magnitud = int(limpio, base)
    for digito in limpio:
        int(digito, base)
    return magnitud


def capturar_entrada_base(valor: Any, base: int) -> tuple[bool, str, int]:
    """Normaliza signo/prefijo y devuelve texto y magnitud; lanza ValueError si falla."""
    if base not in BASES_NUMERICAS.values():
        raise ValueError(f"Base {base} no soportada.")
    texto = str(valor)
    if len(texto) > LONGITUD_MAXIMA_ENTRADA_BASES:
        raise ValueError(
            f"El valor supera {LONGITUD_MAXIMA_ENTRADA_BASES} caracteres. "
            "Introduce un número más corto."
        )
    limpio = texto.strip().replace(" ", "").replace("_", "").upper()
    es_negativo = limpio.startswith("-")
    if es_negativo or limpio.startswith("+"):
        limpio = limpio[1:]
    prefijo = {2: "0B", 8: "0O", 16: "0X"}.get(base)
    if prefijo and limpio.startswith(prefijo):
        limpio = limpio[2:]
    if not limpio:
        raise ValueError("El valor ingresado está vacío.")
    try:
        magnitud = _capturar_magnitud_base(limpio, base)
    except ValueError:
        raise ValueError(f"Valor inválido para la base {base}.") from None
    return es_negativo, limpio, magnitud


def validar_entrada_base(valor: Any, base: int) -> tuple[bool, str]:
    """Orienta con la misma captura del conversor y devuelve validez y mensaje."""
    try:
        capturar_entrada_base(valor, base)
    except ValueError as error:
        return False, str(error)
    return True, "Entrada válida."


def validar_datos_transferencia_matriz(
    datos: Any,
    dimension_maxima: int,
) -> tuple[bool, str]:
    """Valida una matriz cuadrada para transferencia segura entre vistas."""
    if not isinstance(datos, list) or not datos:
        return False, "La estructura de matriz no contiene datos válidos."

    dimension = len(datos)
    if dimension > dimension_maxima:
        return False, f"La dimensión ({dimension}) supera el límite permitido ({dimension_maxima})."

    for fila in datos:
        if not isinstance(fila, list) or len(fila) != dimension:
            return False, "La matriz no es cuadrada o sus filas son irregulares."

    return True, "Datos de matriz conformes."


def validar_datos_transferencia_vectores(
    vectores: Any,
    min_vectores: int = 1,
    max_vectores: int = 10,
) -> tuple[bool, str]:
    """Valida una lista de vectores numéricos para transferencia entre vistas."""
    if not isinstance(vectores, list) or len(vectores) < min_vectores:
        return False, f"Se requieren al menos {min_vectores} vectores."

    if len(vectores) > max_vectores:
        return False, f"Se permite un máximo de {max_vectores} vectores."

    longitud_esperada = len(vectores[0]) if isinstance(vectores[0], list) else 0
    if longitud_esperada == 0:
        return False, "Los vectores no pueden estar vacíos."

    for vector in vectores:
        if not isinstance(vector, list) or len(vector) != longitud_esperada:
            return False, "Todos los vectores deben tener la misma dimensión."

    return True, "Datos de vectores conformes."
