"""Validación estructural y presupuesto de tamaño para la inversa exacta por adjunta."""
from fractions import Fraction

from src.backend.constantes import DIMENSION_MAXIMA_COFACTORES, DIMENSION_MAXIMA_INVERSA
from src.backend.modelos.matriz import Matriz
from .contrato_adjunta import CODIGO_DIMENSION_EXCEDIDA, CODIGO_ENTRADA_INVALIDA, CodigoAdjunta

# El presupuesto conjunto acota los productos de denominadores y su escritura en la traza.
MAXIMO_BITS_DATOS_ADJUNTA = 4096


def validar_entrada_adjunta(matriz: object) -> tuple[CodigoAdjunta, str, int] | None:
    """Devuelve código, mensaje y dimensión ante entrada inválida; None si admite el cálculo."""
    if not isinstance(matriz, Matriz):
        return CODIGO_ENTRADA_INVALIDA, "Se esperaba una matriz exacta.", 0
    if not all(type(valor) is int for valor in (matriz.filas, matriz.columnas)):
        return CODIGO_ENTRADA_INVALIDA, "Las dimensiones deben ser enteros, sin booleanos.", 0
    dimension = matriz.filas
    if dimension != matriz.columnas:
        mensaje = (
            "La matriz debe ser cuadrada para la inversa por adjunta: "
            f"recibido {dimension}×{matriz.columnas}."
        )
        return CODIGO_ENTRADA_INVALIDA, mensaje, dimension
    if not 1 <= dimension <= DIMENSION_MAXIMA_COFACTORES:
        mensaje = (
            f"La inversa por adjunta admite hasta {DIMENSION_MAXIMA_COFACTORES} filas. "
            f"Usa Gauss-Jordan hasta {DIMENSION_MAXIMA_INVERSA} si necesitas una matriz mayor."
        )
        return CODIGO_DIMENSION_EXCEDIDA, mensaje, dimension
    mensaje = _validar_datos(matriz)
    return (CODIGO_ENTRADA_INVALIDA, mensaje, dimension) if mensaje is not None else None


def _validar_datos(matriz: Matriz) -> str | None:
    if not isinstance(matriz.datos, list) or len(matriz.datos) != matriz.filas:
        return "Los datos deben contener una lista por cada fila de la matriz."
    for fila in matriz.datos:
        if not isinstance(fila, list) or len(fila) != matriz.columnas:
            return "Cada fila debe ser una lista con todas las columnas de la matriz."
    return _validar_valores(matriz.datos)


def _validar_valores(datos: list[list]) -> str | None:
    bits_acumulados = 0
    for fila in datos:
        for valor in fila:
            if isinstance(valor, bool) or not isinstance(valor, (int, Fraction)):
                return "Las celdas deben ser enteros o fracciones exactas; no se admite booleano ni flotante."
            bits_acumulados += valor.numerator.bit_length() + valor.denominator.bit_length()
            if bits_acumulados > MAXIMO_BITS_DATOS_ADJUNTA:
                return (
                    f"Los datos exceden el presupuesto conjunto de {MAXIMO_BITS_DATOS_ADJUNTA} bits "
                    "para numeradores y denominadores. Reduce la cantidad de dígitos y vuelve a calcular."
                )
    return None
