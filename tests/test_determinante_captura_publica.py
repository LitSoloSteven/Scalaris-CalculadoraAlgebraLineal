"""Captura pública validada de determinante con aritmética exacta y LU acotado."""
from fractions import Fraction

import pytest

from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante


@pytest.mark.parametrize("datos,esperado,singular", [
    ([["1001/1000"]], Fraction(1001, 1000), False),
    ([[1, 2], [2, 4]], Fraction(0), True),
    ([[0, 1], [1, 0]], Fraction(-1), False),
])
def test_captura_preserva_valor_signo_y_singularidad(datos, esperado, singular):
    """El acceso de interfaz utiliza el resolutor existente sin redondear fracciones."""
    resultado = ControladorDeterminante.procesar_captura({"dimension": len(datos), "datos": datos})
    assert resultado["estado"] == "EXITO"
    assert resultado["metodo"] == "lu"
    assert resultado["determinante"] == esperado
    assert resultado["es_singular"] is singular
    assert resultado["pasos"]


@pytest.mark.parametrize("captura", [
    {"dimension": 51, "datos": []},
    {"dimension": 1, "datos": [["abc"]]},
    {"dimension": 2, "datos": [[1], [2]]},
])
def test_captura_invalida_devuelve_error_sin_ejecutar_resolutor(monkeypatch, captura):
    """Los errores de forma, tamaño o celda preceden el cálculo."""
    def fallar(*argumentos, **opciones):
        """Detecta cualquier cálculo improcedente tras una captura inválida."""
        raise AssertionError("No debe calcular datos inválidos")
    monkeypatch.setattr(ControladorDeterminante, "procesar", fallar)
    resultado = ControladorDeterminante.procesar_captura(captura)
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"]
