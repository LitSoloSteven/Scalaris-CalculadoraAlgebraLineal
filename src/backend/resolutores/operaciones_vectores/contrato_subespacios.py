"""Contratos tipados y validacion de entradas para el analisis de subespacios."""
from collections.abc import Mapping
from fractions import Fraction
from typing import Literal, TypedDict, Union
import unicodedata

from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS,
    DIMENSION_MAXIMA_VECTORES,
    DIMENSION_MINIMA,
    LONGITUD_MAXIMA_CELDA,
)
from src.backend.modelos.matriz import Matriz

MODO_GENERADORES = "generadores"
MODO_RESTRICCIONES = "restricciones"


class EntradaGeneradores(TypedDict):
    """Conjunto finito de generadores columna de R^n con sus etiquetas en orden."""

    modo: Literal["generadores"]
    dimension_ambiente: int
    generadores: tuple[Matriz, ...]
    etiquetas: tuple[str, ...]


class EntradaRestricciones(TypedDict):
    """Sistema A x = b cuyas soluciones describen un conjunto de R^n."""

    modo: Literal["restricciones"]
    dimension_ambiente: int
    matriz_a: Matriz
    vector_b: tuple[Fraction, ...]


EntradaSubespacio = Union[EntradaGeneradores, EntradaRestricciones]


class ContextoRestricciones(TypedDict):
    """Datos intermedios exactos de la reduccion de un sistema de restricciones."""

    entrada: EntradaRestricciones
    matriz_a: Matriz
    vector_b: tuple[Fraction, ...]
    aumentada: Matriz
    reduccion: dict
    pasos: tuple[dict, ...]
    rango: int
    pivotes: tuple[int, ...]
    libres: tuple[int, ...]


class TestigoSubespacio(TypedDict):
    """Razon exacta por la que un conjunto no es un subespacio vectorial."""

    tipo: str
    indice_fila: int | None
    coeficientes: tuple[Fraction, ...]
    termino_independiente: Fraction
    valor_izquierdo: Fraction
    descripcion: str


class ResultadoSubespacio(TypedDict):
    """Resultado completo con todas las claves; en restricciones las matrices son [A|b]."""

    estado: str
    modo: str | None
    clasificacion: str | None
    codigo: str
    mensaje: str
    dimension_ambiente: int | None
    es_subespacio: bool | None
    contiene_origen: bool | None
    es_vacio: bool | None
    rango: int | None
    rango_aumentada: int | None
    base: tuple[tuple[Fraction, ...], ...] | None
    dimension: int | None
    indices_generadores_base: tuple[int, ...]
    etiquetas_generadores_base: tuple[str, ...]
    columnas_pivote: tuple[int, ...]
    columnas_libres: tuple[int, ...]
    particular: tuple[Fraction, ...] | None
    direcciones: tuple[tuple[Fraction, ...], ...] | None
    dimension_afin: int | None
    testigo: TestigoSubespacio | None
    matriz_original: Matriz | None
    matriz_reducida: Matriz | None
    pasos: tuple[dict, ...]
    comprobaciones: tuple[dict, ...]


class ErrorCapturaSubespacio(ValueError):
    """Error de captura con codigo interno y ubicacion del campo invalido."""

    def __init__(self, codigo: str, mensaje: str, ubicacion: str | None = None) -> None:
        """Guarda el diagnostico y compone un mensaje con la ubicacion cuando existe."""
        self.codigo = codigo
        self.ubicacion = ubicacion
        detalle = f"{mensaje} Ubicacion: {ubicacion}." if ubicacion else mensaje
        super().__init__(detalle)


class ErrorVerificacionSubespacio(ValueError):
    """Error interno cuando una comprobacion exacta del resultado no se cumple."""


def validar_dimension_ambiente(
    valor: object, maximo: int = DIMENSION_MAXIMA_VECTORES
) -> int:
    """Devuelve la dimension ambiente acotada al maximo del modo o lanza error de captura."""
    if type(valor) is not int or not DIMENSION_MINIMA <= valor <= maximo:
        raise ErrorCapturaSubespacio(
            "DIMENSION_INVALIDA",
            f"La dimension ambiente debe ser un entero entre {DIMENSION_MINIMA} y {maximo}.",
            "dimension_ambiente",
        )
    return valor


def validar_etiqueta(etiqueta: object, ubicacion: str = "etiquetas") -> str:
    """Devuelve una etiqueta breve y visible o lanza error de captura con su ubicacion."""
    if (
        not isinstance(etiqueta, str)
        or not etiqueta.strip()
        or len(etiqueta) > LONGITUD_MAXIMA_CELDA
    ):
        raise ErrorCapturaSubespacio(
            "ETIQUETA_INVALIDA",
            f"Cada etiqueta debe ser texto no vacio de hasta {LONGITUD_MAXIMA_CELDA} caracteres.",
            ubicacion,
        )
    if any(unicodedata.category(caracter).startswith("C") for caracter in etiqueta):
        raise ErrorCapturaSubespacio(
            "ETIQUETA_INVALIDA",
            "Las etiquetas no admiten caracteres de control ni de formato invisible.",
            ubicacion,
        )
    return etiqueta


def validar_entrada_subespacio(entrada: object) -> None:
    """Revalida una entrada tipada antes de analizarla y lanza error de captura si no encaja."""
    if not isinstance(entrada, Mapping):
        raise ErrorCapturaSubespacio(
            "ENTRADA_INVALIDA", "La entrada debe ser un objeto de analisis.", "entrada"
        )
    modo = entrada.get("modo")
    if modo == "generadores":
        _validar_generadores(entrada)
    elif modo == "restricciones":
        _validar_restricciones(entrada)
    else:
        raise ErrorCapturaSubespacio(
            "MODO_INVALIDO", "El modo debe ser generadores o restricciones.", "modo"
        )


def _validar_generadores(entrada: Mapping) -> None:
    dimension = validar_dimension_ambiente(entrada.get("dimension_ambiente"))
    generadores = _secuencia(entrada.get("generadores"), "generadores")
    if not DIMENSION_MINIMA <= len(generadores) <= DIMENSION_MAXIMA_VECTORES:
        raise ErrorCapturaSubespacio(
            "CANTIDAD_INVALIDA",
            f"La entrada admite entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_VECTORES} generadores.",
            "generadores",
        )
    etiquetas = _secuencia(entrada.get("etiquetas"), "etiquetas")
    if len(etiquetas) != len(generadores):
        raise ErrorCapturaSubespacio(
            "ETIQUETAS_INCOMPLETAS", "Cada generador necesita una etiqueta.", "etiquetas"
        )
    for indice, generador in enumerate(generadores):
        _validar_vector_columna(generador, dimension, f"generadores[{indice}]")
    for indice, etiqueta in enumerate(etiquetas):
        validar_etiqueta(etiqueta, f"etiquetas[{indice}]")


def _validar_restricciones(entrada: Mapping) -> None:
    dimension = validar_dimension_ambiente(
        entrada.get("dimension_ambiente"), DIMENSION_MAXIMA_SISTEMAS
    )
    matriz_a = entrada.get("matriz_a")
    if not isinstance(matriz_a, Matriz) or matriz_a.columnas != dimension:
        raise ErrorCapturaSubespacio(
            "MATRIZ_INVALIDA", f"La matriz A debe tener {dimension} columnas.", "matriz_a"
        )
    if not DIMENSION_MINIMA <= matriz_a.filas <= DIMENSION_MAXIMA_SISTEMAS:
        raise ErrorCapturaSubespacio(
            "FILAS_INVALIDAS",
            f"La matriz A admite entre {DIMENSION_MINIMA} y {DIMENSION_MAXIMA_SISTEMAS} filas.",
            "matriz_a",
        )
    for fila in range(matriz_a.filas):
        for columna in range(matriz_a.columnas):
            _validar_escalar_exacto(
                matriz_a.obtener(fila, columna), f"matriz_a[{fila}][{columna}]"
            )
    vector_b = _secuencia(entrada.get("vector_b"), "vector_b")
    if len(vector_b) != matriz_a.filas:
        raise ErrorCapturaSubespacio(
            "TERMINOS_INVALIDOS",
            f"El vector b debe tener {matriz_a.filas} terminos independientes.",
            "vector_b",
        )
    for indice, valor in enumerate(vector_b):
        _validar_escalar_exacto(valor, f"vector_b[{indice}]")


def _validar_vector_columna(valor: object, dimension: int, ubicacion: str) -> None:
    if not isinstance(valor, Matriz) or valor.columnas != 1 or valor.filas != dimension:
        raise ErrorCapturaSubespacio(
            "VECTOR_INVALIDO",
            f"Se esperaba un vector columna de dimension {dimension}.",
            ubicacion,
        )
    for fila in range(dimension):
        _validar_escalar_exacto(valor.obtener(fila, 0), f"{ubicacion}[{fila}]")


def _validar_escalar_exacto(valor: object, ubicacion: str) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, Fraction)):
        raise ErrorCapturaSubespacio(
            "VALOR_NO_EXACTO",
            "Los coeficientes deben ser enteros o fracciones exactas.",
            ubicacion,
        )


def _secuencia(valor: object, ubicacion: str) -> tuple | list:
    """Devuelve la secuencia original ya validada, sin copiarla."""
    if not isinstance(valor, (tuple, list)):
        raise ErrorCapturaSubespacio(
            "SECUENCIA_INVALIDA", "Se esperaba una secuencia de elementos.", ubicacion
        )
    return valor
