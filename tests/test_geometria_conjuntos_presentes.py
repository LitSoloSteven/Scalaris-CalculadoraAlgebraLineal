"""Presencia explícita del conjunto solución para espacios completos y puntos."""
import json

import pytest

from src.frontend.controladores.geometria.controlador_geometria import ControladorGeometria


@pytest.mark.parametrize("coeficientes,independientes", [
    ([["0", "0"]], ["0"]),
    ([["0", "0", "0"]], ["0"]),
    ([["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], ["-1", "10", "1/2"]),
])
def test_conjunto_solucion_existe_antes_de_leer_sus_campos(coeficientes, independientes):
    """Cada escenario exige un conjunto presente aunque sus campos se comprueben aparte."""
    carga = json.dumps({"matriz_a": coeficientes, "vector_b": independientes})
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["conjunto_solucion"] is not None
