"""Pruebas unitarias para el clasificador de pasos elementales de Gauss-Jordan."""
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def test_clasificar_pivote():
    """Identifica la operación de selección de pivote y sus coordenadas."""
    res = clasificar_paso("Pivote seleccionado en Fila 2, Columna 2")
    assert res["tipo"] == "pivote"
    assert res["fila_origen"] == 1
    assert res["columna"] == 1


def test_clasificar_eliminacion():
    """Identifica la operación de eliminación y extrae filas y factor escalar."""
    res = clasificar_paso("Fila 3 = Fila 3 − (2) · Fila 1")
    assert res["tipo"] == "eliminacion"
    assert res["fila_origen"] == 2
    assert res["fila_destino"] == 0
    assert res["texto_valor"] == "2"


def test_clasificar_intercambio():
    """Identifica la operación de intercambio de filas y sus índices."""
    res = clasificar_paso("Intercambio: Fila 1 ↔ Fila 3")
    assert res["tipo"] == "intercambio"
    assert res["fila_origen"] == 0
    assert res["fila_destino"] == 2
