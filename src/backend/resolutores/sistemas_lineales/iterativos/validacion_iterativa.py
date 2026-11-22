"""Validación exacta compartida por los métodos iterativos de sistemas lineales."""
from collections.abc import Mapping
from dataclasses import replace
from fractions import Fraction
from itertools import islice

from .contrato_iterativo import CampoIterativo, EntradaIterativa
from .conversion_iterativa import convertir_escalar, convertir_secuencia, preparar_cuadricula
from .modelos_iterativos import (
    DatosValidacion, EntradaPreparada, FalloValidacion, ParametrosValidacion, crear_fallo,
)

__all__ = [
    "EntradaPreparada",
    "FalloValidacion",
    "ParametrosValidacion",
    "preparar_captura",
    "preparar_entrada",
]


def preparar_entrada(
    entrada: object, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    """Valida la entrada tipada y devuelve una instantánea o el fallo ubicado."""
    if not isinstance(entrada, EntradaIterativa):
        return crear_fallo(
            parametros,
            "entrada",
            f"La entrada debe cumplir el contrato del método de {parametros.nombre_metodo}.",
        )
    matriz = preparar_cuadricula(entrada.matriz_a, parametros)
    if isinstance(matriz, FalloValidacion):
        return matriz
    return _preparar_sistema(
        DatosValidacion(
            matriz=matriz,
            vector_b=entrada.vector_b,
            vector_inicial=entrada.vector_inicial,
            tolerancia=entrada.tolerancia,
            maximo_iteraciones=entrada.maximo_iteraciones,
        ),
        parametros,
    )


def preparar_captura(
    captura: object, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    """Valida las celdas crudas de A y usa un inicio cero cuando se omite el campo."""
    if not isinstance(captura, Mapping):
        return crear_fallo(
            parametros,
            "entrada",
            f"La captura de {parametros.nombre_metodo} debe contener campos con nombre.",
        )
    matriz = preparar_cuadricula(captura.get("matriz_a"), parametros)
    if isinstance(matriz, FalloValidacion):
        return matriz
    return _preparar_sistema(
        DatosValidacion(
            matriz=matriz,
            vector_b=captura.get("vector_b"),
            vector_inicial=captura.get("vector_inicial", (0,) * len(matriz)),
            tolerancia=captura.get("tolerancia"),
            maximo_iteraciones=captura.get("maximo_iteraciones"),
        ),
        parametros,
    )


def _preparar_sistema(
    datos: DatosValidacion, parametros: ParametrosValidacion,
) -> EntradaPreparada | FalloValidacion:
    if isinstance(datos.matriz, FalloValidacion):
        return datos.matriz
    dominancia = _es_estrictamente_dominante(datos.matriz)
    dimension = len(datos.matriz)
    vector_b = _validar_vector(datos.vector_b, "vector_b", dimension, parametros)
    if isinstance(vector_b, FalloValidacion):
        return replace(vector_b, dominancia_estricta=dominancia)
    vector_inicial = _validar_vector(
        datos.vector_inicial, "vector_inicial", dimension, parametros,
    )
    if isinstance(vector_inicial, FalloValidacion):
        return replace(vector_inicial, dominancia_estricta=dominancia)
    tolerancia = _validar_tolerancia(datos.tolerancia, parametros)
    if isinstance(tolerancia, FalloValidacion):
        return replace(tolerancia, dominancia_estricta=dominancia)
    maximo = _validar_maximo(datos.maximo_iteraciones, parametros)
    if isinstance(maximo, FalloValidacion):
        return replace(maximo, dominancia_estricta=dominancia)
    diagonal_nula = _buscar_diagonal_nula(datos.matriz)
    if diagonal_nula is not None:
        return _fallo_diagonal(diagonal_nula, dominancia, parametros)
    return EntradaPreparada(
        matriz=datos.matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
        dominancia_estricta=dominancia,
    )


def _validar_vector(
    valor: object,
    campo: CampoIterativo,
    dimension: int,
    parametros: ParametrosValidacion,
) -> tuple[Fraction, ...] | FalloValidacion:
    """Copia el vector y comprueba su longitud antes de leer sus celdas."""
    if not isinstance(valor, (tuple, list)):
        return crear_fallo(
            parametros, campo, f"El vector debe ser una tupla o lista de {dimension} valores.",
        )
    copia = tuple(islice(iter(valor), dimension + 1))
    if len(copia) != dimension:
        return crear_fallo(
            parametros, campo, f"El vector no tiene exactamente {dimension} valores.",
        )
    return convertir_secuencia(copia, campo, parametros)


def _validar_tolerancia(
    valor: object, parametros: ParametrosValidacion,
) -> Fraction | FalloValidacion:
    """Exige una tolerancia racional estrictamente positiva y de tamaño admitido."""
    fraccion = convertir_escalar(valor, "tolerancia", parametros)
    if isinstance(fraccion, FalloValidacion):
        return fraccion
    if fraccion <= 0:
        return crear_fallo(
            parametros, "tolerancia", "La tolerancia debe ser estrictamente positiva.",
        )
    return fraccion


def _validar_maximo(
    valor: object, parametros: ParametrosValidacion,
) -> int | FalloValidacion:
    """Exige un entero positivo dentro del tope documentado de iteraciones."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return crear_fallo(
            parametros, "maximo_iteraciones",
            "El máximo de iteraciones debe ser un entero.",
        )
    if not 1 <= valor <= parametros.maximo_iteraciones:
        return crear_fallo(
            parametros,
            "maximo_iteraciones",
            f"El máximo de iteraciones debe estar entre 1 y {parametros.maximo_iteraciones}.",
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


def _fallo_diagonal(
    indice: int, dominancia: bool, parametros: ParametrosValidacion,
) -> FalloValidacion:
    """Construye el diagnóstico de una diagonal nula con su fila y columna."""
    posicion = indice + 1
    return FalloValidacion(
        codigo="DIAGONAL_NULA",
        diagnostico=parametros.crear_diagnostico(
            mensaje=(
                f"El coeficiente diagonal A[{posicion},{posicion}] debe ser distinto de cero."
            ),
            campo="matriz_a",
            fila=posicion,
            columna=posicion,
        ),
        dominancia_estricta=dominancia,
    )
