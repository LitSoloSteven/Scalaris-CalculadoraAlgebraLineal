"""Señales de sistemas a partir de los diccionarios reales de captura matricial."""
from types import SimpleNamespace

import pytest

from src.frontend.vistas.sistemas_lineales.vista_sistemas_lineales import VistaSistemasLineales


@pytest.mark.parametrize("valor,etiqueta", [("1/3", None), ("abc", "A[1,1]")])
def test_productor_recoge_celdas_sin_ocultar_senales(valor, etiqueta):
    """La captura matricial produce señales y conserva la primera entrada inválida."""
    vista = SimpleNamespace(pestanas_modo=SimpleNamespace(value="Matriz"),
                            cuadricula=SimpleNamespace(_cache_coeficientes={(0, 0): valor}, _cache_independientes={0: "2/3"}, filas=1, columnas=1),
                            ultimo_resultado=None)
    senales = VistaSistemasLineales.obtener_senales_ia(vista)
    assert senales is not None
    assert senales.herramienta == "sistemas" and senales.estado == "sin_resultado"
    assert senales.banderas == frozenset()
    assert (senales.invalida.etiqueta if senales.invalida else None) == etiqueta
