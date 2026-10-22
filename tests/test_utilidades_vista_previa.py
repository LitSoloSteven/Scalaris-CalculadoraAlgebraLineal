"""Casos límite del auxiliar de caracterización de la vista previa."""
import pytest
from tests.comun_vista_previa import construir_vista_previa_latex


def test_fila_con_columnas_adicionales_conserva_recorrido_original():
    """La validación conserva la anchura de la primera fila del contrato heredado."""
    matriz, ecuaciones = construir_vista_previa_latex([["1"], ["1", "abc"]], ["1", "2"])
    assert r"\begin{array}{c|c}" in matriz
    assert r"\begin{cases}" in ecuaciones
    assert "x_{1} = 2" in ecuaciones


def test_fila_mas_corta_conserva_excepcion_de_indice():
    """Una fila más corta conserva el error del auxiliar original."""
    with pytest.raises(IndexError):
        construir_vista_previa_latex([["1", "1"], ["1"]], ["1", "2"])


def test_celda_invalida_muestra_aviso_y_matriz_saneada():
    """El valor inválido se representa con interrogación y bloquea ecuaciones."""
    matriz, mensaje = construir_vista_previa_latex([["abc"]], ["1"])
    assert r"\color{gray}{?}" in matriz
    assert mensaje == "Corrige los valores inválidos para ver las ecuaciones."


def test_matriz_sin_filas_devuelve_aviso_de_vacio():
    """La ausencia de filas no construye un entorno LaTeX."""
    assert construir_vista_previa_latex([], []) == (None, "La matriz está vacía.")
