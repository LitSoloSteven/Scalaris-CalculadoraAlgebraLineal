"""Comprueba los estados independientes de los factores durante la eliminacion."""
from fractions import Fraction

import pytest

from src.backend.modelos.construcciones import identidad
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.factorizacion_lu import factorizar_lu


@pytest.mark.parametrize("datos", [
    [[1, 2, 3], [4, 5, 6], [7, 8, 10]],
    [[1, 2], [2, 4]],
    [[1, 2, 3], [4, 5, 6]],
])
def test_instantaneas_independientes_y_dimensiones(datos):
    matriz = Matriz(len(datos), len(datos[0]), datos)
    resultado = factorizar_lu(matriz)
    pasos = resultado["traza"]
    for clave in ("permutacion", "inferior"):
        instantaneas = [paso[clave] for paso in pasos]
        assert all(isinstance(valor, Matriz) and valor.filas == matriz.filas
                   and valor.columnas == matriz.filas for valor in instantaneas)
        assert len({id(valor) for valor in instantaneas + [resultado[clave]]}) == len(pasos) + 1
        anterior = instantaneas[0].datos[0][0]
        final = resultado[clave].datos[0][0]
        instantaneas[-1].establecer(0, 0, 99)
        assert instantaneas[0].obtener(0, 0) == anterior
        assert resultado[clave].obtener(0, 0) == final


def test_intercambio_y_multiplicador_reflejan_eventos():
    resultado = factorizar_lu(Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 10]]))
    pasos = resultado["traza"]
    indice = next(indice for indice, paso in enumerate(pasos) if paso["tipo"] == "intercambio")
    assert pasos[indice - 1]["permutacion"] == identidad(3)
    assert pasos[indice]["permutacion"] != identidad(3)
    eliminacion = next(paso for paso in pasos if paso["tipo"] == "eliminacion")
    assert eliminacion["inferior"].obtener(1, 0) == Fraction(4, 7)


def test_comprobacion_conserva_sus_pasos_originales():
    resultado = factorizar_lu(Matriz(1, 1, [[1]]))
    assert all(set(paso) == {"tipo", "descripcion", "detalle_latex", "explicacion"}
               for paso in resultado["comprobacion"]["traza"])
