"""Pruebas de dominio para Gauss e inversión de matrices."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.utilidades.validadores import ValidadorMatriz


def test_gauss_modulo():
    """Valida la resolución de un sistema compatible determinado por Gauss."""
    datos_crudos = [
        [2.0, 1.0, -1.0, 8.0],
        [-3.0, -1.0, 2.0, -11.0],
        [-2.0, 1.0, 2.0, -3.0],
    ]

    dim_valida, _ = ValidadorMatriz.validar_dimensiones(3, 4)
    datos_validos, _ = ValidadorMatriz.validar_datos_matriz(datos_crudos, 3, 4)
    assert dim_valida and datos_validos

    matriz_aumentada = Matriz(3, 4, datos_crudos)
    resolutor = ResolutorGauss(matriz_aumentada)
    resultado = resolutor.resolver()

    assert resultado["estado"] == "SOLUCION_UNICA"
    assert len(resultado["pasos"]) > 0
    assert resultado["solucion"] is not None
    assert resultado["solucion"] == ["2", "3", "-1"]


def test_gauss_con_fracciones():
    """Valida la resolución de Gauss a partir de cadenas fraccionarias exactas."""
    datos_con_cadenas = [
        ["2", "1/3", "-1", "8"],
        ["-3/2", "-1", "2", "-11"],
        ["-2", "1", "2/5", "-3"],
    ]

    valido, datos_parseados, _ = ValidadorMatriz.validar_y_parsear_matriz_cruda(
        datos_con_cadenas, 3, 4
    )
    assert valido

    matriz = Matriz(3, 4, datos_parseados)
    resolutor = ResolutorGauss(matriz)
    resultado = resolutor.resolver()

    assert resultado["estado"] == "SOLUCION_UNICA"
    assert len(resultado["pasos"]) > 0


def test_resolutor_matriz_inversa():
    """Valida el cálculo de matriz inversa y sus propiedades matemáticas."""
    resolutor = ResolutorInversa()

    mat_2x2 = Matriz(2, 2, [[1, 2], [3, 4]])
    res_2x2 = resolutor.resolver(mat_2x2)
    assert res_2x2["estado"] == "EXITO"
    assert res_2x2["determinante"] == Fraction(-2)
    assert res_2x2["inversa"].datos == [
        [Fraction(-2), Fraction(1)],
        [Fraction(3, 2), Fraction(-1, 2)],
    ]
    assert res_2x2["paso_verificacion"]["coincide"] is True
    assert res_2x2["paso_verificacion_inverso"]["coincide"] is True
    assert res_2x2["paso_propiedad_transpuesta"]["coincide"] is True
    assert len(res_2x2["pasos"]) > 0

    mat_sing = Matriz(2, 2, [[1, 2], [2, 4]])
    res_sing = resolutor.resolver(mat_sing)
    assert res_sing["estado"] == "SINGULAR"
    assert res_sing["determinante"] == 0
    assert res_sing["inversa"] is None

    mat_1x1 = Matriz(1, 1, [[5]])
    res_1x1 = resolutor.resolver(mat_1x1)
    assert res_1x1["estado"] == "EXITO"
    assert res_1x1["inversa"].datos == [[Fraction(1, 5)]]

    mat_2x3 = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    res_2x3 = resolutor.resolver(mat_2x3)
    assert res_2x3["estado"] == "ERROR"

    res_no_latex = resolutor.resolver(mat_2x2, construir_detalle_latex=False)
    assert res_no_latex["estado"] == "EXITO"
    assert res_no_latex["inversa"].datos == res_2x2["inversa"].datos
    assert all(s["detalle_latex"] is None for s in res_no_latex["pasos"])
