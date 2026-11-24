"""Oraculos exactos de menores, cofactores, adjunta e inversa."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa.inversa_adjunta import (
    calcular_inversa_adjunta,
)

CLAVES_RESULTADO = {
    "estado", "codigo", "mensaje", "metodo", "dimension", "matriz_a",
    "determinante", "menores", "cofactores", "adjunta", "inversa",
    "detalle_cofactores", "traza", "comprobaciones", "nodos_cofactores",
    "limite_nodos",
}


def test_resultado_conserva_todas_las_claves():
    """La salida exitosa, singular y erronea comparte el mismo contrato."""
    for datos, esperado in (([[2]], "EXITO"), ([[0]], "SINGULAR"), ([[1, 2], [3, 4]], "EXITO")):
        resultado = calcular_inversa_adjunta(Matriz(len(datos), len(datos), datos))
        assert set(resultado) == CLAVES_RESULTADO
        assert resultado["estado"] == esperado
        assert resultado["metodo"] == "adjunta"


def test_uno_por_uno_invertible_usa_menor_vacio():
    """El orden 1 no crea una matriz vacia y devuelve el reciproco exacto."""
    resultado = calcular_inversa_adjunta(Matriz(1, 1, [[2]]))
    assert resultado["estado"] == "EXITO"
    assert resultado["codigo"] == "INVERSA_CALCULADA"
    assert resultado["determinante"] == Fraction(2)
    assert resultado["menores"].datos == [[Fraction(1)]]
    assert resultado["cofactores"].datos == [[Fraction(1)]]
    assert resultado["adjunta"].datos == [[Fraction(1)]]
    assert resultado["inversa"].datos == [[Fraction(1, 2)]]
    detalle = resultado["detalle_cofactores"][0]
    assert detalle["menor_vacio"] is True
    assert detalle["matriz_menor"] is None
    assert detalle["filas_originales"] == ()


def test_uno_por_uno_cero_es_singular_con_adjunta():
    """El cero de orden 1 conserva adjunta unitaria y no intenta dividir."""
    resultado = calcular_inversa_adjunta(Matriz(1, 1, [[0]]))
    assert resultado["estado"] == "SINGULAR"
    assert resultado["codigo"] == "MATRIZ_SINGULAR"
    assert resultado["determinante"] == Fraction(0)
    assert resultado["adjunta"].datos == [[Fraction(1)]]
    assert resultado["inversa"] is None
    assert resultado["detalle_cofactores"][0]["menor_vacio"] is True


def test_dos_por_dos_entera_contra_oraculo_literal():
    """La matriz de cofactores, su transpuesta y la inversa son exactas."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[1, 2], [3, 4]]))
    assert resultado["determinante"] == Fraction(-2)
    assert resultado["menores"].datos == [[4, 3], [2, 1]]
    assert resultado["cofactores"].datos == [[4, -3], [-2, 1]]
    assert resultado["adjunta"].datos == [[4, -2], [-3, 1]]
    assert resultado["inversa"].datos == [[-2, 1], [Fraction(3, 2), Fraction(-1, 2)]]
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])


def test_dos_por_dos_fraccionaria_contra_oraculo_literal():
    """Las fracciones de entrada y salida se conservan sin pasar por flotante."""
    matriz = Matriz(2, 2, [["1/2", "1/3"], ["2/3", "3/4"]])
    resultado = calcular_inversa_adjunta(matriz)
    assert resultado["determinante"] == Fraction(11, 72)
    assert resultado["cofactores"].datos == [[Fraction(3, 4), Fraction(-2, 3)],
                                              [Fraction(-1, 3), Fraction(1, 2)]]
    assert resultado["adjunta"].datos == [[Fraction(3, 4), Fraction(-1, 3)],
                                          [Fraction(-2, 3), Fraction(1, 2)]]
    assert resultado["inversa"].datos == [[Fraction(54, 11), Fraction(-24, 11)],
                                          [Fraction(-48, 11), Fraction(36, 11)]]


def test_tres_por_tres_no_simetrica_verifica_transposicion():
    """Los indices y el signo se comprueban con una matriz sin simetria."""
    resultado = calcular_inversa_adjunta(Matriz(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]]))
    assert resultado["determinante"] == Fraction(1)
    assert resultado["inversa"].datos == [[-24, 18, 5], [20, -15, -4], [-5, 4, 1]]
    assert resultado["adjunta"].datos == resultado["inversa"].datos
    assert resultado["menores"].datos[0] == [-24, -20, -5]
    assert resultado["cofactores"].datos[0] == [-24, 20, -5]


def test_singular_dos_por_dos_conserva_adjunta():
    """Una matriz dependiente devuelve el procedimiento completo sin division."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[1, 2], [2, 4]]))
    assert resultado["estado"] == "SINGULAR"
    assert resultado["determinante"] == Fraction(0)
    assert resultado["cofactores"].datos == [[4, -2], [-2, 1]]
    assert resultado["adjunta"].datos == [[4, -2], [-2, 1]]
    assert resultado["inversa"] is None
    assert len(resultado["comprobaciones"]) == 1


def test_matriz_nula_dos_por_dos_tiene_cofactores_nulos():
    """La matriz nula conserva menores, cofactores y adjunta nulos."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[0, 0], [0, 0]]))
    assert resultado["estado"] == "SINGULAR"
    assert resultado["menores"].datos == [[0, 0], [0, 0]]
    assert resultado["cofactores"].datos == [[0, 0], [0, 0]]
    assert resultado["adjunta"].datos == [[0, 0], [0, 0]]
    assert resultado["determinante"] == Fraction(0)


@pytest.mark.parametrize("datos", ([[1, 2, 3], [0, 1, 4], [5, 6, 0]],
                                  [["1/2", "1/3"], ["2/3", "3/4"]]))
def test_matriz_de_entrada_no_se_modifica(datos):
    """El motor clona la fuente y no expone la misma lista de datos."""
    matriz = Matriz(len(datos), len(datos), datos)
    original = matriz.clonar()
    resultado = calcular_inversa_adjunta(matriz)
    assert matriz == original
    assert resultado["matriz_a"] == original
    assert resultado["matriz_a"] is not matriz
