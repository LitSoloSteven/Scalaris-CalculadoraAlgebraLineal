"""Cobertura de ventanas matriciales y errores fuera del área visible."""
import pytest
from src.ai.contexto import describir_matriz


def test_ventana_cuenta_errores_fuera_de_celdas_visibles():
    """El recorte conserva el recuento de errores de toda la matriz."""
    filas = [[" 1 ", "2", "abc"], ["3", "4", "5"], ["6", "xyz", "7"]]
    resultado = describir_matriz(filas, maximo_completa=1, ventana=2)
    assert resultado == {
        "filas": 3, "columnas": 3, "ventana": [2, 2],
        "datos": [["1", "2"], ["3", "4"]], "invalidos": 2,
    }


def test_ventana_vacia_conserva_dimensiones_y_recuento():
    """La ventana de tamaño cero conserva información de dimensiones y errores."""
    resultado = describir_matriz([["1", "abc"], ["2", "3"]], maximo_completa=1, ventana=0)
    assert resultado == {"filas": 2, "columnas": 2, "ventana": [0, 0], "datos": [], "invalidos": 1}


def test_ventana_irregular_conserva_error_de_indice():
    """Una fila corta mantiene el error del descriptor original."""
    with pytest.raises(IndexError):
        describir_matriz([["1", "2"], ["3"]], maximo_completa=1)


def test_ventana_valida_omite_contador_de_errores():
    """La matriz válida conserva únicamente su descriptor de ventana."""
    resultado = describir_matriz([["1", "2"], ["3", "4"]], maximo_completa=1, ventana=1)
    assert resultado == {"filas": 2, "columnas": 2, "ventana": [1, 1], "datos": [["1"]]}
