"""Invariantes matematicos de PA=LU, incluidos ceros, singularidad y rectangulares."""
from fractions import Fraction
from random import Random

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.factorizacion_lu import factorizar_lu


def _producto(izquierda, derecha):
    return [[sum(izquierda[fila][indice] * derecha[indice][columna] for indice in range(len(derecha)))
             for columna in range(len(derecha[0]))] for fila in range(len(izquierda))]


def _comprobar_factores(datos):
    matriz = Matriz(len(datos), len(datos[0]), datos)
    original = [fila[:] for fila in matriz.datos]
    resultado = factorizar_lu(matriz)
    inferior, superior, permutacion = [resultado[clave].datos for clave in ("inferior", "superior", "permutacion")]
    assert _producto(permutacion, original) == _producto(inferior, superior)
    _comprobar_triangularidad(inferior, superior, matriz.columnas)
    _comprobar_permutacion(permutacion)
    assert resultado["comprobacion"]["coincide"] is True
    assert matriz.datos == original
    assert resultado["convencion"] == "PA=LU"
    assert sum(paso["tipo"] == "verificacion" for paso in resultado["traza"]) == matriz.filas * matriz.columnas + 2
    return resultado


def _comprobar_triangularidad(inferior, superior, columnas):
    assert all(inferior[fila][fila] == 1 for fila in range(len(inferior)))
    assert all(inferior[fila][columna] == 0 for fila in range(len(inferior)) for columna in range(fila + 1, len(inferior)))
    posiciones = [next((indice for indice, valor in enumerate(fila) if valor), len(fila)) for fila in superior]
    pivotes = [indice for indice in posiciones if indice < columnas]
    assert pivotes == sorted(set(pivotes))
    assert posiciones == sorted(posiciones)


def _comprobar_permutacion(permutacion):
    assert all(sum(fila) == 1 and set(fila) <= {0, 1} for fila in permutacion)
    assert all(sum(fila[columna] for fila in permutacion) == 1 for columna in range(len(permutacion)))


@pytest.mark.parametrize("datos", [
    [["7/13"]], [[0]], [[0, 1], [1, 0]], [[1, 2], [2, 4]],
    [[0, 1, 2], [0, 2, 5]], [[1, 2], [3, 4], [5, 6]],
    [[0, 0, 0], [0, 0, 0]], [[4, 1, 0], [2, 0, 1], [1, 2, 2]],
    [["1/2", "2/3"], ["3/4", "4/5"]],
])
def test_lu_conserva_invariantes_y_desarrolla_comprobacion(datos):
    """La factorizacion cumple convencion, triangularidad, escalonamiento y producto exacto."""
    _comprobar_factores(datos)


def test_intercambio_intermedio_permuta_multiplicadores_previos():
    """Una permutacion posterior al primer pivote tambien reordena la parte construida de L."""
    resultado = _comprobar_factores([[4, 1, 0], [2, 0, 1], [1, 2, 2]])
    assert resultado["inferior"].obtener(1, 0) == Fraction(1, 4)
    assert resultado["inferior"].obtener(2, 0) == Fraction(1, 2)
    assert any("Intercambio" in paso["descripcion"] for paso in resultado["traza"])


def test_lu_explica_las_operaciones_en_el_texto_visible_del_reproductor():
    """La explicacion visible incluye el intercambio, pivote o formula de fila correspondiente."""
    resultado = factorizar_lu(Matriz(2, 2, [[1, 2], [3, 4]]))
    operaciones = [paso for paso in resultado["traza"] if paso["tipo"] in ("intercambio", "pivote", "eliminacion")]
    assert operaciones
    assert all(paso["descripcion"] in paso["explicacion"] for paso in operaciones)


def test_lu_invariantes_en_familia_racional_reproducible():
    """Prueba distintas dimensiones con racionales y pivotes repetidos sin fijar factores arbitrarios."""
    generador = Random(817)
    for filas in range(1, 6):
        for columnas in range(1, 6):
            for repeticion in range(3):
                datos = [[Fraction(generador.randint(-3, 3), generador.randint(1, 7))
                          for columna in range(columnas)] for fila in range(filas)]
                _comprobar_factores(datos)


