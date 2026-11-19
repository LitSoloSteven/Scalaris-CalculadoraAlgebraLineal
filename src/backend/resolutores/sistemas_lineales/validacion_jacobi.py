"""Validación exacta de la entrada del método iterativo de Jacobi."""
from collections.abc import Mapping
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import islice

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS, LONGITUD_MAXIMA_CADENA_NUMERO,
    MENSAJE_NUMERO_DEMASIADO_LARGO,
)
from src.backend.modelos.entrada_numerica import convertir_numero_exacto
from src.backend.modelos.matriz import Matriz

from .contrato_jacobi import (
    CampoJacobi, CodigoJacobi, DiagnosticoJacobi, EntradaJacobi,
)
from .limites_jacobi import (
    MAXIMO_BITS_ENTRADA_JACOBI, MAXIMO_ITERACIONES_JACOBI, fraccion_admitida,
)


@dataclass(frozen=True, kw_only=True)
class EntradaPreparadaJacobi:
    """Instantánea inmutable de A, b, el inicio y los parámetros ya validados."""

    matriz: tuple[tuple[Fraction, ...], ...]
    vector_b: tuple[Fraction, ...]
    vector_inicial: tuple[Fraction, ...]
    tolerancia: Fraction
    maximo_iteraciones: int
    dominancia_estricta: bool


@dataclass(frozen=True, kw_only=True)
class FalloValidacionJacobi:
    """Fallo de entrada con su código, diagnóstico y dominancia si pudo evaluarse."""

    codigo: CodigoJacobi
    diagnostico: DiagnosticoJacobi
    dominancia_estricta: bool | None = None


def preparar_entrada(
    entrada: EntradaJacobi,
) -> EntradaPreparadaJacobi | FalloValidacionJacobi:
    """Valida la entrada completa y devuelve una instantánea o el fallo ubicado."""
    if not isinstance(entrada, EntradaJacobi):
        return _fallo("entrada", "La entrada debe cumplir el contrato del método de Jacobi.")
    return _preparar_sistema(
        _validar_matriz(entrada.matriz_a), entrada.vector_b, entrada.vector_inicial,
        entrada.tolerancia, entrada.maximo_iteraciones,
    )


def preparar_captura(captura: object) -> EntradaPreparadaJacobi | FalloValidacionJacobi:
    """Valida las celdas crudas de A y usa un inicio cero cuando se omite el campo."""
    if not isinstance(captura, Mapping):
        return _fallo("entrada", "La captura de Jacobi debe contener campos con nombre.")
    datos = captura.get("matriz_a")
    if not isinstance(datos, (list, tuple)):
        return _fallo("matriz_a", "La matriz A debe ser una cuadrícula de coeficientes.")
    filas = tuple(islice(datos, DIMENSION_MAXIMA_SISTEMAS + 1))
    dimension = _orden_matriz(len(filas), len(filas))
    if isinstance(dimension, FalloValidacionJacobi):
        return dimension
    return _preparar_sistema(
        _validar_cuadricula(filas, dimension), captura.get("vector_b"),
        captura.get("vector_inicial", (0,) * dimension),
        captura.get("tolerancia"), captura.get("maximo_iteraciones"),
    )


def _preparar_sistema(
    matriz: tuple[tuple[Fraction, ...], ...] | FalloValidacionJacobi,
    independientes: object, inicial: object, umbral: object, maximo_solicitado: object,
) -> EntradaPreparadaJacobi | FalloValidacionJacobi:
    if isinstance(matriz, FalloValidacionJacobi):
        return matriz
    dominancia = _es_estrictamente_dominante(matriz)
    dimension = len(matriz)
    vector_b = _validar_vector(independientes, "vector_b", dimension)
    if isinstance(vector_b, FalloValidacionJacobi):
        return replace(vector_b, dominancia_estricta=dominancia)
    vector_inicial = _validar_vector(inicial, "vector_inicial", dimension)
    if isinstance(vector_inicial, FalloValidacionJacobi):
        return replace(vector_inicial, dominancia_estricta=dominancia)
    tolerancia = _validar_tolerancia(umbral)
    if isinstance(tolerancia, FalloValidacionJacobi):
        return replace(tolerancia, dominancia_estricta=dominancia)
    maximo = _validar_maximo(maximo_solicitado)
    if isinstance(maximo, FalloValidacionJacobi):
        return replace(maximo, dominancia_estricta=dominancia)
    diagonal_nula = _buscar_diagonal_nula(matriz)
    if diagonal_nula is not None:
        return _fallo_diagonal(diagonal_nula, dominancia)
    return EntradaPreparadaJacobi(
        matriz=matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
        dominancia_estricta=dominancia,
    )


def _validar_matriz(
    matriz_a: object,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacionJacobi:
    """Comprueba tipo, forma cuadrada, tamaño y celdas exactas de A."""
    if not isinstance(matriz_a, Matriz):
        return _fallo("matriz_a", "La matriz A no tiene un formato admitido.")
    dimension = _orden_matriz(getattr(matriz_a, "filas", None), getattr(matriz_a, "columnas", None))
    if isinstance(dimension, FalloValidacionJacobi):
        return dimension
    return _validar_cuadricula(getattr(matriz_a, "datos", None), dimension)


def _orden_matriz(filas: object, columnas: object) -> int | FalloValidacionJacobi:
    if (not isinstance(filas, int) or not isinstance(columnas, int)
            or isinstance(filas, bool) or isinstance(columnas, bool)):
        return _fallo("matriz_a", "La matriz A no tiene dimensiones válidas.")
    if (not 1 <= filas <= DIMENSION_MAXIMA_SISTEMAS
            or not 1 <= columnas <= DIMENSION_MAXIMA_SISTEMAS):
        return _fallo("matriz_a", f"El orden de A debe estar entre 1 y {DIMENSION_MAXIMA_SISTEMAS}.")
    if filas != columnas:
        return _fallo("matriz_a", "La matriz A debe ser cuadrada.")
    return filas


def _validar_cuadricula(
    datos: object, dimension: int,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacionJacobi:
    if not isinstance(datos, (list, tuple)):
        return _fallo("matriz_a", "La matriz A no tiene datos válidos.")
    copia = tuple(
        tuple(islice(fila, dimension + 1))
        if isinstance(fila, (list, tuple)) else fila
        for fila in islice(datos, dimension + 1)
    )
    if not copia:
        return _fallo("matriz_a", "La matriz A no puede estar vacía.")
    if len(copia) != dimension:
        return _fallo("matriz_a", "La matriz A no tiene la cantidad de filas declarada.")
    return _convertir_matriz(copia, dimension)


def _convertir_matriz(
    datos: tuple, columnas: int,
) -> tuple[tuple[Fraction, ...], ...] | FalloValidacionJacobi:
    """Convierte la instantánea de A y ubica las filas inválidas."""
    filas_convertidas = []
    for indice_fila, fila in enumerate(datos, 1):
        if not isinstance(fila, (list, tuple)):
            return _fallo(
                "matriz_a", f"La fila {indice_fila} de A no es una secuencia válida.",
                indice_fila,
            )
        if len(fila) != columnas:
            unidad = "columna" if columnas == 1 else "columnas"
            mensaje = f"La fila {indice_fila} de A debe tener exactamente {columnas} {unidad}."
            return _fallo("matriz_a", mensaje, indice_fila)
        fila_convertida = _convertir_secuencia(fila, "matriz_a", indice_fila)
        if isinstance(fila_convertida, FalloValidacionJacobi):
            return fila_convertida
        filas_convertidas.append(fila_convertida)
    return tuple(filas_convertidas)


def _convertir_secuencia(
    valores: tuple | list, campo: CampoJacobi, fila: int | None = None,
) -> tuple[Fraction, ...] | FalloValidacionJacobi:
    """Convierte una secuencia y devuelve la primera celda inválida con su ubicación."""
    convertidas = []
    for indice, valor in enumerate(valores, 1):
        ubicacion_fila = fila if fila is not None else indice
        ubicacion_columna = indice if fila is not None else None
        fraccion = _convertir_escalar(valor, campo, ubicacion_fila, ubicacion_columna)
        if isinstance(fraccion, FalloValidacionJacobi):
            return fraccion
        convertidas.append(fraccion)
    return tuple(convertidas)


def _convertir_escalar(
    valor: object,
    campo: CampoJacobi,
    fila: int | None = None,
    columna: int | None = None,
) -> Fraction | FalloValidacionJacobi:
    """Convierte un valor exacto y rechaza booleanos, flotantes o tamaños excesivos."""
    if isinstance(valor, bool):
        return _fallo(campo, "No se admiten valores booleanos.", fila, columna)
    if not isinstance(valor, (int, str, Fraction)):
        return _fallo(campo, "El valor debe ser un número exacto.", fila, columna)
    if isinstance(valor, str) and len(valor) > LONGITUD_MAXIMA_CADENA_NUMERO:
        return _fallo(campo, MENSAJE_NUMERO_DEMASIADO_LARGO, fila, columna)
    valido, fraccion, mensaje = convertir_numero_exacto(valor)
    if not valido:
        return _fallo(campo, mensaje, fila, columna)
    if not fraccion_admitida(fraccion, MAXIMO_BITS_ENTRADA_JACOBI):
        return _fallo(
            campo,
            f"El número excede el tamaño máximo de {MAXIMO_BITS_ENTRADA_JACOBI} bits "
            "en numerador o denominador.",
            fila,
            columna,
        )
    return fraccion


def _validar_vector(
    valor: object, campo: CampoJacobi, dimension: int,
) -> tuple[Fraction, ...] | FalloValidacionJacobi:
    """Copia el vector y comprueba su longitud antes de leer sus celdas."""
    if not isinstance(valor, (tuple, list)):
        return _fallo(campo, f"El vector debe ser una tupla o lista de {dimension} valores.")
    copia = tuple(islice(iter(valor), dimension + 1))
    if len(copia) != dimension:
        return _fallo(campo, f"El vector no tiene exactamente {dimension} valores.")
    return _convertir_secuencia(copia, campo)


def _validar_tolerancia(valor: object) -> Fraction | FalloValidacionJacobi:
    """Exige una tolerancia racional estrictamente positiva y de tamaño admitido."""
    fraccion = _convertir_escalar(valor, "tolerancia")
    if isinstance(fraccion, FalloValidacionJacobi):
        return fraccion
    if fraccion <= 0:
        return _fallo("tolerancia", "La tolerancia debe ser estrictamente positiva.")
    return fraccion


def _validar_maximo(valor: object) -> int | FalloValidacionJacobi:
    """Exige un entero positivo dentro del tope documentado de iteraciones."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return _fallo("maximo_iteraciones", "El máximo de iteraciones debe ser un entero.")
    if not 1 <= valor <= MAXIMO_ITERACIONES_JACOBI:
        return _fallo(
            "maximo_iteraciones",
            f"El máximo de iteraciones debe estar entre 1 y {MAXIMO_ITERACIONES_JACOBI}.",
        )
    return valor


def _buscar_diagonal_nula(matriz: tuple[tuple[Fraction, ...], ...]) -> int | None:
    """Devuelve el índice de la primera ecuación con diagonal cero, si existe."""
    for indice, fila in enumerate(matriz):
        if fila[indice] == 0:
            return indice
    return None


def _es_estrictamente_dominante(matriz: tuple[tuple[Fraction, ...], ...]) -> bool:
    """Comprueba |a_ii| > suma de |a_ij| fuera de la diagonal en cada fila."""
    for indice, fila in enumerate(matriz):
        suma_fuera = sum(
            abs(valor) for posicion, valor in enumerate(fila) if posicion != indice
        )
        if abs(fila[indice]) <= suma_fuera:
            return False
    return True


def _fallo_diagonal(indice: int, dominancia: bool) -> FalloValidacionJacobi:
    """Construye el diagnóstico de una diagonal nula con su fila y columna."""
    posicion = indice + 1
    return FalloValidacionJacobi(
        codigo="DIAGONAL_NULA",
        diagnostico=DiagnosticoJacobi(
            mensaje=(
                f"El coeficiente diagonal A[{posicion},{posicion}] debe ser distinto de cero."
            ),
            campo="matriz_a",
            fila=posicion,
            columna=posicion,
        ),
        dominancia_estricta=dominancia,
    )


def _fallo(
    campo: CampoJacobi,
    mensaje: str,
    fila: int | None = None,
    columna: int | None = None,
) -> FalloValidacionJacobi:
    """Construye un fallo de entrada con el campo y las coordenadas conocidas."""
    return FalloValidacionJacobi(
        codigo="ENTRADA_INVALIDA",
        diagnostico=DiagnosticoJacobi(mensaje=mensaje, campo=campo, fila=fila, columna=columna),
    )
