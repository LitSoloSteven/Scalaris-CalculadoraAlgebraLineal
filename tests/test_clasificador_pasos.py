"""Pruebas unitarias para el clasificador de pasos elementales de Gauss-Jordan."""
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def test_clasificar_pivote():
    """Identifica la operación de selección de pivote y sus coordenadas."""
    res = clasificar_paso("Pivote seleccionado en Fila 2, Columna 2")
    assert res["kind"] == "pivote"
    assert res["row1"] == 1
    assert res["col"] == 1


def test_clasificar_eliminacion():
    """Identifica la operación de eliminación y extrae filas y factor escalar."""
    res = clasificar_paso("Fila 3 = Fila 3 − (2) · Fila 1")
    assert res["kind"] == "eliminacion"
    assert res["row1"] == 2
    assert res["row2"] == 0
    assert res["val_str"] == "2"


def test_clasificar_intercambio():
    """Identifica la operación de intercambio de filas y sus índices."""
    res = clasificar_paso("Intercambio: Fila 1 ↔ Fila 3")
    assert res["kind"] == "intercambio"
    assert res["row1"] == 0
    assert res["row2"] == 2
