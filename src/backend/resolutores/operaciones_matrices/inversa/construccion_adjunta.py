"""Construccion exacta de menores, cofactores, determinante y adjunta."""
from fractions import Fraction
from typing import Literal, TypedDict

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.operaciones.construcciones import transpuesta
from src.backend.resolutores.operaciones_matrices.determinante.cofactores import (
    ExpansionCofactores,
    construir_menor,
    seleccionar_fila,
)
from .contrato_adjunta import DetalleCofactor


class ConstruccionAdjunta(TypedDict):
    """Datos exactos intermedios compartidos por la salida y la traza."""

    detalles: tuple[DetalleCofactor, ...]
    menores: Matriz
    cofactores: Matriz
    adjunta: Matriz
    determinante: Fraction
    fila_expansion: int
    nodos: int


def construir_adjunta(datos: list[list[Fraction]]) -> ConstruccionAdjunta:
    """Calcula los n² menores, sus cofactores, la adjunta y el determinante exacto."""
    dimension = len(datos)
    expansor = ExpansionCofactores()
    detalles = _construir_detalles(datos, dimension, expansor)
    menores = _matriz_desde_detalles(detalles, dimension, "valor_menor")
    cofactores = _matriz_desde_detalles(detalles, dimension, "cofactor")
    fila_expansion = seleccionar_fila(datos)
    determinante = sum(
        (datos[fila_expansion][columna] * cofactores.obtener(fila_expansion, columna)
         for columna in range(dimension)),
        start=Fraction(0),
    )
    return {
        "detalles": detalles,
        "menores": menores,
        "cofactores": cofactores,
        "adjunta": transpuesta(cofactores),
        "determinante": determinante,
        "fila_expansion": fila_expansion,
        "nodos": expansor.nodos,
    }


def _construir_detalles(
    datos: list[list[Fraction]], dimension: int, expansor: ExpansionCofactores
) -> tuple[DetalleCofactor, ...]:
    if dimension == 1:
        return (_detalle_unico(),)
    return tuple(
        _detalle(datos, dimension, expansor, fila, columna)
        for fila in range(dimension)
        for columna in range(dimension)
    )


def _detalle_unico() -> DetalleCofactor:
    return {
        "fila": 0,
        "columna": 0,
        "filas_originales": (),
        "columnas_originales": (),
        "matriz_menor": None,
        "valor_menor": Fraction(1),
        "signo": 1,
        "cofactor": Fraction(1),
        "menor_vacio": True,
    }


def _detalle(
    datos: list[list[Fraction]],
    dimension: int,
    expansor: ExpansionCofactores,
    fila: int,
    columna: int,
) -> DetalleCofactor:
    menor = construir_menor(datos, fila, columna)
    matriz_menor = Matriz(dimension - 1, dimension - 1, menor)
    valor = expansor.calcular_valor(matriz_menor)
    signo = -1 if (fila + columna) % 2 else 1
    return {
        "fila": fila,
        "columna": columna,
        "filas_originales": tuple(indice for indice in range(dimension) if indice != fila),
        "columnas_originales": tuple(indice for indice in range(dimension) if indice != columna),
        "matriz_menor": matriz_menor,
        "valor_menor": valor,
        "signo": signo,
        "cofactor": signo * valor,
        "menor_vacio": False,
    }


def _matriz_desde_detalles(
    detalles: tuple[DetalleCofactor, ...],
    dimension: int,
    clave: Literal["valor_menor", "cofactor"],
) -> Matriz:
    return Matriz(
        dimension,
        dimension,
        [[detalles[fila * dimension + columna][clave] for columna in range(dimension)]
         for fila in range(dimension)],
    )
