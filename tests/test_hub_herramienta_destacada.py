"""Elección de la herramienta destacada del Hub."""
import dataclasses

import pytest

from src.frontend.vistas.hub import _recent
from src.frontend.vistas.hub._recent import pick_featured


def test_historial_valido_selecciona_primera_herramienta():
    """La primera herramienta válida determina el punto focal."""
    tool, has_history = pick_featured(["inversa", "romanos"])
    assert tool.id == "inversa"
    assert has_history is True


def test_lista_vacia_selecciona_sistemas():
    """El historial vacío selecciona sistemas sin indicar historial."""
    tool, has_history = pick_featured([])
    assert tool.id == "sistemas"
    assert has_history is False


@pytest.mark.parametrize("raw", [None, "inversa", 42, {"a": 1}, (), 3.5])
def test_valores_ajenos_a_lista_seleccionan_sistemas(raw):
    """Las entradas de otros tipos usan la selección predeterminada."""
    tool, has_history = pick_featured(raw)
    assert tool.id == "sistemas"
    assert has_history is False


def test_identificadores_desconocidos_seleccionan_sistemas():
    """Un historial sin herramientas conocidas usa sistemas."""
    tool, has_history = pick_featured(["zzz", "nope"])
    assert tool.id == "sistemas"
    assert has_history is False


def test_entradas_invalidas_se_omiten():
    """Se elige la primera herramienta válida tras entradas inválidas."""
    tool, has_history = pick_featured([1, None, "zzz", ["x"], "romanos"])
    assert tool.id == "romanos"
    assert has_history is True


def test_duplicados_seleccionan_primera_aparicion():
    """El historial repetido conserva una selección válida."""
    tool, has_history = pick_featured(["bases", "bases", "bases"])
    assert tool.id == "bases"
    assert has_history is True


def test_herramienta_desactivada_se_omite(monkeypatch):
    """El historial pasa a la siguiente herramienta habilitada."""
    real = _recent.tool_by_id

    def fake(tool_id):
        tool = real(tool_id)
        if tool_id == "inversa":
            return dataclasses.replace(tool, enabled=False)
        return tool

    monkeypatch.setattr(_recent, "tool_by_id", fake)
    tool, has_history = pick_featured(["inversa", "vectores"])
    assert tool.id == "vectores"
    assert has_history is True


def test_datos_inutilizables_no_lanzan_excepcion():
    """Las entradas no utilizables mantienen la selección de respaldo."""
    for raw in ([object()], [[]], [{}], ["", " "], [True, False]):
        tool, has_history = pick_featured(raw)
        assert tool.id == "sistemas"
        assert has_history is False
