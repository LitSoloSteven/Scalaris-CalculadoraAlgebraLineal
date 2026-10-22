"""Elección de la herramienta destacada del inicio."""
import dataclasses

import pytest

from src.frontend.controladores.inicio import _recientes
from src.frontend.controladores.inicio._recientes import elegir_destacada


def test_historial_valido_selecciona_primera_herramienta():
    """La primera herramienta válida determina el punto focal."""
    herramienta, hay_historial = elegir_destacada(["inversa", "romanos"])
    assert herramienta.identificador == "inversa"
    assert hay_historial is True


def test_lista_vacia_selecciona_sistemas():
    """El historial vacío selecciona sistemas sin indicar historial."""
    herramienta, hay_historial = elegir_destacada([])
    assert herramienta.identificador == "sistemas"
    assert hay_historial is False


@pytest.mark.parametrize("datos_crudos", [None, "inversa", 42, {"a": 1}, (), 3.5])
def test_valores_ajenos_a_lista_seleccionan_sistemas(datos_crudos):
    """Las entradas de otros tipos usan la selección predeterminada."""
    herramienta, hay_historial = elegir_destacada(datos_crudos)
    assert herramienta.identificador == "sistemas"
    assert hay_historial is False


def test_identificadores_desconocidos_seleccionan_sistemas():
    """Un historial sin herramientas conocidas usa sistemas."""
    herramienta, hay_historial = elegir_destacada(["zzz", "nope"])
    assert herramienta.identificador == "sistemas"
    assert hay_historial is False


def test_entradas_invalidas_se_omiten():
    """Se elige la primera herramienta válida tras entradas inválidas."""
    herramienta, hay_historial = elegir_destacada([1, None, "zzz", ["x"], "romanos"])
    assert herramienta.identificador == "romanos"
    assert hay_historial is True


def test_duplicados_seleccionan_primera_aparicion():
    """El historial repetido conserva una selección válida."""
    herramienta, hay_historial = elegir_destacada(["bases", "bases", "bases"])
    assert herramienta.identificador == "bases"
    assert hay_historial is True


def test_herramienta_desactivada_se_omite(monkeypatch):
    """El historial pasa a la siguiente herramienta habilitada."""
    real = _recientes.herramienta_por_identificador

    def simular_herramienta_desactivada(identificador_herramienta):
        """Conserva el catálogo y desactiva únicamente la herramienta inversa."""
        herramienta = real(identificador_herramienta)
        if identificador_herramienta == "inversa":
            return dataclasses.replace(herramienta, habilitada=False)
        return herramienta

    monkeypatch.setattr(_recientes, "herramienta_por_identificador", simular_herramienta_desactivada)
    herramienta, hay_historial = elegir_destacada(["inversa", "vectores"])
    assert herramienta.identificador == "vectores"
    assert hay_historial is True


def test_datos_inutilizables_no_lanzan_excepcion():
    """Las entradas no utilizables mantienen la selección de respaldo."""
    for datos_crudos in ([object()], [[]], [{}], ["", " "], [True, False]):
        herramienta, hay_historial = elegir_destacada(datos_crudos)
        assert herramienta.identificador == "sistemas"
        assert hay_historial is False
