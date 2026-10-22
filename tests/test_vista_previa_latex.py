"""Caracterización del LaTeX de matriz aumentada y ecuaciones."""
import pytest
from tests.comun_vista_previa import construir_vista_previa_latex


def test_vista_previa_cierra_matriz_sin_llaves_dobles():
    """El cierre del entorno matricial usa las llaves correctas."""
    matriz_a = [["1", "2"], ["3", "4"]]
    vector_b = ["5", "6"]
    matriz_latex, _ = construir_vista_previa_latex(matriz_a, vector_b)
    assert r"\begin{array}" in matriz_latex
    assert r"\end{array}" in matriz_latex
    assert "{{array}}" not in matriz_latex
    assert "}}" not in matriz_latex


def test_vista_previa_celdas_vacias_muestra_matriz_y_aviso():
    """Las celdas vacías producen una matriz de ceros sin ecuaciones."""
    matriz_a = [["", ""], ["", ""]]
    vector_b = ["", ""]
    matriz_latex, mensaje = construir_vista_previa_latex(matriz_a, vector_b)
    assert r"\begin{array}{cc|c}" in matriz_latex
    assert r"\end{array}" in matriz_latex
    assert "{{array}}" not in matriz_latex
    assert mensaje == "No hay ecuaciones válidas."


@pytest.mark.parametrize("dimension", range(1, 11))
def test_vista_previa_dimensiones_uno_a_diez(dimension):
    """La matriz se muestra en todas las dimensiones y las ecuaciones hasta el límite."""
    matriz_vacia = [["" for _ in range(dimension)] for _ in range(dimension)]
    vector_vacio = ["" for _ in range(dimension)]
    matriz_latex, resultado = construir_vista_previa_latex(matriz_vacia, vector_vacio)
    assert r"\begin{array}" in matriz_latex
    assert r"\end{array}" in matriz_latex
    assert "{{array}}" not in matriz_latex
    assert resultado == "No hay ecuaciones válidas." or "demasiado grande" in resultado
    matriz_llena = [[str(i * dimension + j + 1) for j in range(dimension)] for i in range(dimension)]
    vector_lleno = [str(i + 1) for i in range(dimension)]
    matriz_llena_latex, resultado_lleno = construir_vista_previa_latex(matriz_llena, vector_lleno)
    assert r"\begin{array}" in matriz_llena_latex
    assert r"\end{array}" in matriz_llena_latex
    assert "{{array}}" not in matriz_llena_latex
    if dimension * dimension <= 48:
        assert r"\begin{cases}" in resultado_lleno
        assert r"\end{cases}" in resultado_lleno
        assert "{{cases}}" not in resultado_lleno
    else:
        assert resultado_lleno == "Sistema demasiado grande para vista previa en ecuaciones."
