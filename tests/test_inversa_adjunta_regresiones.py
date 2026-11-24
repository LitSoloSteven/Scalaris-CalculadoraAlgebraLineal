"""Paridad exacta con determinante, Gauss-Jordan y productos de identidad."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.operaciones.calculo_matricial import multiplicar_matrices
from src.backend.modelos.operaciones.construcciones import identidad
from src.backend.resolutores.operaciones_matrices.determinante.determinante import (
    ResolutorDeterminante,
)
from src.backend.resolutores.operaciones_matrices.inversa.inversa import ResolutorInversa
from src.backend.resolutores.operaciones_matrices.inversa.inversa_adjunta import (
    calcular_inversa_adjunta,
)

CORPUS = [
    [[1]], [[2]], [[0]], [[Fraction(1, 3)]],
    [[1, 2], [3, 4]], [[4, 6], [3, 8]], [[0, 1], [1, 0]],
    [[1, 2], [2, 4]], [["1/2", "1/3"], ["2/3", "3/4"]],
    [["1/1001", 0], [0, "1/1001"]],
    [[1, 2, 3], [0, 1, 4], [5, 6, 0]],
    [[1, 2, 3], [2, 4, 6], [7, 8, 9]],
]


def _comprobar_productos(matriz: Matriz, inversa: Matriz) -> None:
    esperado = identidad(matriz.filas)
    assert multiplicar_matrices(matriz, inversa).datos == esperado.datos
    assert multiplicar_matrices(inversa, matriz).datos == esperado.datos


def _comprobar_adjunta(matriz: Matriz, resultado: dict) -> None:
    determinante = resultado["determinante"]
    esperado = Matriz(
        matriz.filas,
        matriz.filas,
        [[determinante if fila == columna else Fraction(0) for columna in range(matriz.filas)]
         for fila in range(matriz.filas)],
    )
    producto = multiplicar_matrices(matriz, resultado["adjunta"])
    assert producto.datos == esperado.datos


@pytest.mark.parametrize("datos", CORPUS)
def test_determinante_y_adjunta_coinciden_con_el_motor_lu(datos):
    """El determinante por cofactores y el de eliminacion son identicos."""
    matriz = Matriz(len(datos), len(datos), datos)
    resultado = calcular_inversa_adjunta(matriz)
    esperado = ResolutorDeterminante.resolver_lu(matriz)["determinante"]
    assert resultado["determinante"] == esperado
    _comprobar_adjunta(matriz, resultado)


@pytest.mark.parametrize("datos", CORPUS)
def test_paridad_con_gauss_jordan_y_productos_de_identidad(datos):
    """La inversa coincide con la ruta heredada y cumple ambos productos."""
    matriz = Matriz(len(datos), len(datos), datos)
    resultado = calcular_inversa_adjunta(matriz)
    heredado = ResolutorInversa().resolver(matriz)
    if resultado["determinante"] == 0:
        assert resultado["estado"] == "SINGULAR"
        assert resultado["inversa"] is None
        assert heredado["estado"] == "SINGULAR"
        return
    assert resultado["estado"] == "EXITO"
    assert resultado["inversa"].datos == heredado["inversa"].datos
    _comprobar_productos(matriz, resultado["inversa"])


@pytest.mark.parametrize("datos", CORPUS)
def test_entrada_permanece_intacta_tras_el_calculo(datos):
    """La copia exacta de entrada no comparte celdas con la matriz de trabajo."""
    matriz = Matriz(len(datos), len(datos), datos)
    original = matriz.clonar()
    calcular_inversa_adjunta(matriz)
    assert matriz == original
    assert matriz.datos == original.datos


def test_fraccion_con_denominador_grande_se_conserva():
    """La division exacta no reconstruye el denominador con tolerancias."""
    matriz = Matriz(2, 2, [[Fraction(1, 1001), 0], [0, Fraction(1, 1001)]])
    resultado = calcular_inversa_adjunta(matriz)
    assert resultado["determinante"] == Fraction(1, 1002001)
    assert resultado["inversa"].datos == [[1001, 0], [0, 1001]]
    _comprobar_productos(matriz, resultado["inversa"])


def test_comprobaciones_nombran_las_tres_relaciones_exactas():
    """La salida invertible conserva las claves de las tres comprobaciones."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[4, 6], [3, 8]]))
    assert [comprobacion["clave"] for comprobacion in resultado["comprobaciones"]] == [
        "a_adjunta", "derecha", "izquierda"
    ]
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
    assert all(comprobacion["detalle_latex"] for comprobacion in resultado["comprobaciones"])
