"""Conversión exacta y copia acotada de matrices y vectores iterativos."""
from fractions import Fraction
from itertools import islice

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS, LONGITUD_MAXIMA_CADENA_NUMERO,
    MENSAJE_NUMERO_DEMASIADO_LARGO,
)
from src.backend.modelos.escalares.entrada_numerica import convertir_numero_exacto

from .contrato_iterativo import CampoIterativo
from .limites_iterativos import fraccion_admitida
from .modelos_iterativos import (
    FalloValidacion, ParametrosValidacion, crear_fallo, crear_fallo_cuadricula,
)


def preparar_cuadricula(
    datos: object, parametros: ParametrosValidacion,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacion:
    """Copia como máximo el orden admitido y convierte la matriz exacta."""
    if not isinstance(datos, (list, tuple)):
        return crear_fallo_cuadricula(
            parametros,
            "La matriz A debe ser una lista o tupla de filas con los coeficientes originales.",
        )
    filas = tuple(islice(datos, DIMENSION_MAXIMA_SISTEMAS + 1))
    dimension = len(filas)
    if dimension == 0:
        return crear_fallo_cuadricula(parametros, "La matriz A no puede estar vacía.")
    if dimension > DIMENSION_MAXIMA_SISTEMAS:
        return crear_fallo_cuadricula(
            parametros,
            f"El orden de A debe estar entre 1 y {DIMENSION_MAXIMA_SISTEMAS}.",
        )
    copia = tuple(
        tuple(islice(fila, dimension + 1)) if isinstance(fila, (list, tuple)) else fila
        for fila in filas
    )
    return convertir_matriz(copia, dimension, parametros)


def convertir_matriz(
    datos: tuple, columnas: int, parametros: ParametrosValidacion,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacion:
    """Convierte la instantánea de A y ubica las filas inválidas."""
    filas_convertidas = []
    for indice_fila, fila in enumerate(datos, 1):
        if not isinstance(fila, (list, tuple)):
            return crear_fallo_cuadricula(
                parametros,
                f"La fila {indice_fila} de A no es una secuencia válida.",
                indice_fila,
            )
        if len(fila) != columnas:
            unidad = "columna" if columnas == 1 else "columnas"
            mensaje = f"La fila {indice_fila} de A debe tener exactamente {columnas} {unidad}."
            return crear_fallo_cuadricula(parametros, mensaje, indice_fila)
        fila_convertida = convertir_secuencia(
            fila, "matriz_a", parametros, indice_fila,
        )
        if isinstance(fila_convertida, FalloValidacion):
            return fila_convertida
        filas_convertidas.append(fila_convertida)
    return tuple(filas_convertidas)


def convertir_secuencia(
    valores: tuple | list,
    campo: CampoIterativo,
    parametros: ParametrosValidacion,
    fila: int | None = None,
) -> tuple[Fraction, ...] | FalloValidacion:
    """Convierte una secuencia y devuelve la primera celda inválida con su ubicación."""
    convertidas = []
    for indice, valor in enumerate(valores, 1):
        ubicacion_fila = fila if fila is not None else indice
        ubicacion_columna = indice if fila is not None else None
        fraccion = convertir_escalar(
            valor, campo, parametros, ubicacion_fila, ubicacion_columna,
        )
        if isinstance(fraccion, FalloValidacion):
            return fraccion
        convertidas.append(fraccion)
    return tuple(convertidas)


def convertir_escalar(
    valor: object,
    campo: CampoIterativo,
    parametros: ParametrosValidacion,
    fila: int | None = None,
    columna: int | None = None,
) -> Fraction | FalloValidacion:
    """Convierte un valor exacto y rechaza booleanos, flotantes o tamaños excesivos."""
    if isinstance(valor, bool):
        return crear_fallo(
            parametros, campo, "No se admiten valores booleanos.", fila, columna,
        )
    if not isinstance(valor, (int, str, Fraction)):
        return crear_fallo(
            parametros, campo, "El valor debe ser un número exacto.", fila, columna,
        )
    if isinstance(valor, str) and len(valor) > LONGITUD_MAXIMA_CADENA_NUMERO:
        return crear_fallo(
            parametros, campo, MENSAJE_NUMERO_DEMASIADO_LARGO, fila, columna,
        )
    valido, fraccion, mensaje = convertir_numero_exacto(valor)
    if not valido:
        return crear_fallo(parametros, campo, mensaje, fila, columna)
    if not fraccion_admitida(fraccion, parametros.maximo_bits_entrada):
        return crear_fallo(
            parametros,
            campo,
            f"El número excede el tamaño máximo de {parametros.maximo_bits_entrada} bits "
            "en numerador o denominador.",
            fila,
            columna,
        )
    return fraccion
