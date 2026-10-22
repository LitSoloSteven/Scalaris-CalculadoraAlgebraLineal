"""Orden de la solución y de las ecuaciones en las figuras geométricas."""
import json

import pytest

from src.frontend.controladores.geometria.controlador_geometria import ControladorGeometria
from src.frontend.vistas.geometria._figura_rectas_planos import construir_figura_rectas_planos


@pytest.mark.parametrize('matriz,independiente,nombre', [
    ([['1', '1']], ['2'], 'Conjunto solución (recta)'),
    ([['1', '1', '1']], ['1'], 'Conjunto solución (plano)'),
])
def test_solucion_se_dibuja_antes_de_la_ecuacion(matriz, independiente, nombre):
    """Las mismas recta y plano conservan la precedencia de su traza de solución."""
    carga = json.dumps({'matriz_a': matriz, 'vector_b': independiente})
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    figura = construir_figura_rectas_planos(resultado, tema='papel')
    nombres = [traza.name for traza in figura.data]
    assert nombres.index(nombre) < nombres.index('Ecuación 1')
