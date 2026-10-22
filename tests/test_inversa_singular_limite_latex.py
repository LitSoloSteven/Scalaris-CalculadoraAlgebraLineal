"""La traza singular conserva los datos y respeta el límite de matrices LaTeX."""
from unittest.mock import Mock

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices import inversa


@pytest.mark.parametrize('dimension', [DIMENSION_MAXIMA_LATEX_INVERSA,
                                      DIMENSION_MAXIMA_LATEX_INVERSA + 1, 50])
def test_traza_singular_no_formatea_matrices_fuera_del_limite(monkeypatch, dimension):
    """El límite afecta al formato, conservando determinante, operaciones e instantáneas."""
    datos = [[int(fila == columna) for columna in range(dimension)] for fila in range(dimension)]
    datos[1] = list(datos[0])
    matriz = Matriz(dimension, dimension, datos)
    formatear = Mock(wraps=inversa.matriz_a_latex)
    monkeypatch.setattr(inversa, 'matriz_a_latex', formatear)
    resultado = inversa.ResolutorInversa().resolver(matriz, construir_detalle_latex=False)
    assert resultado['estado'] == 'SINGULAR' and resultado['determinante'] == 0
    assert matriz.datos == datos
    traza = resultado['traza_determinante']
    assert len(traza) > 2 and traza[-1]['detalle_latex'].startswith(r'\det(A)')
    _comprobar_presentacion(traza, dimension, formatear)


def _comprobar_presentacion(traza, dimension, formatear):
    """Conserva los contratos pequeños y verifica instantáneas exactas en tamaños grandes."""
    if dimension > DIMENSION_MAXIMA_LATEX_INVERSA:
        formatear.assert_not_called()
        assert all(paso['matriz'].filas == dimension for paso in traza)
        assert any(paso['operacion'].get('factor') == 1 for paso in traza)
        assert all(not paso['detalle_latex'] for paso in traza[:-1])
        traza[0]['matriz'].establecer(0, 0, 7)
        assert traza[-1]['matriz'].obtener(0, 0) == 1
    else:
        assert formatear.called
        assert all(paso['detalle_latex'] for paso in traza)
