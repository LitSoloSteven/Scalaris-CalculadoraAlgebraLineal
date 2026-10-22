"""Fronteras racionales de igualdad, pivoteo y clasificacion de sistemas."""
from fractions import Fraction

import pytest

from src.backend.constantes import CERO_EPSILON
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
@pytest.mark.parametrize("escala", [Fraction(1, 1001), Fraction(7, 13), Fraction(-3)])
def test_reescalar_ecuaciones_conserva_solucion_exacta(resolutor, escala):
    """Cada resolutor mantiene la solucion al multiplicar todas las ecuaciones."""
    datos = [[2, 1, 5], [1, -1, 1]]
    escalados = [[escala * valor for valor in fila] for fila in datos]
    matriz = Matriz(2, 3, escalados)
    original = tuple(tuple(fila) for fila in matriz.datos)
    resultado = resolutor(matriz).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(2), Fraction(1)]
    assert tuple(tuple(fila) for fila in matriz.datos) == original


@pytest.mark.parametrize("valor", [Fraction(7, 13), 10**18, 0.5])
def test_igualdad_conserva_coincidencia_de_valores_representables(valor):
    """La igualdad acepta valores iguales admitidos por la normalizacion actual."""
    assert Matriz(1, 1, [[valor]]) == Matriz(1, 1, [[valor]])


@pytest.mark.parametrize("valores", [
    (Fraction(1, 10**12), 0),
    (1 + Fraction(1, 10**12), 1),
    (10**18 + 1, 10**18),
])
def test_igualdad_distingue_valores_exactos_cercanos(valores):
    """Dos matrices racionales distintas deben conservar su desigualdad exacta."""
    izquierda, derecha = valores
    assert Matriz(1, 1, [[izquierda]]) != Matriz(1, 1, [[derecha]])


def test_igualdad_admite_enteros_fuera_del_rango_flotante():
    """Comparar enteros iguales no debe requerir una conversion aproximada."""
    entero = 10**400
    assert Matriz(1, 1, [[entero]]) == Matriz(1, 1, [[entero]])


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
@pytest.mark.parametrize("escala", [Fraction(1, 10**12), Fraction(-1, 10**12)])
def test_pivote_racional_pequeno_conserva_solucion_unica(resolutor, escala):
    """Una ecuacion equivalente sigue determinada aunque sus coeficientes sean pequenos."""
    resultado = resolutor(Matriz(1, 2, [[escala, 3 * escala]])).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(3)]


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
def test_eliminacion_anula_coeficiente_en_frontera_epsilon(resolutor):
    """La operacion elemental debe anular el coeficiente racional bajo el pivote."""
    frontera = Fraction.from_float(CERO_EPSILON)
    matriz = Matriz(2, 3, [[1, 0, 1], [frontera, 1, 1]])
    resultado = resolutor(matriz).resolver_reduccion()
    assert resultado["matriz_reducida"].obtener(1, 0) == 0


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
def test_termino_independiente_pequeno_no_es_homogeneo(resolutor):
    """Un termino independiente no nulo debe conservar su semantica y valor exacto."""
    termino = Fraction(1, 10**12)
    resultado = resolutor(Matriz(1, 2, [[1, termino]])).resolver()
    assert resultado["analisis_sistema"]["es_homogeneo"] is False
    assert resultado["solucion_exacta"] == [termino]
