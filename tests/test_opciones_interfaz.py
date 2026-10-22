"""Opciones de interfaz configuradas mediante variables de entorno."""
import pytest
from src.frontend.banderas import panel_lateral_habilitado, navegacion_actualizada, proactivo_habilitado
from tests.comun_opciones_interfaz import comprobar_opciones_configuradas


def test_opciones_predeterminadas_sin_variables_de_entorno(monkeypatch):
    """Las opciones se activan cuando no hay configuración explícita."""
    monkeypatch.delenv("SCALARIS_NAV", raising=False)
    monkeypatch.delenv("SCALARIS_DOCK", raising=False)
    monkeypatch.delenv("SCALARIS_PROACTIVE", raising=False)
    assert navegacion_actualizada() is True
    assert panel_lateral_habilitado() is True
    assert proactivo_habilitado() is True


@pytest.mark.parametrize("valor", ["1", "true", "True", "TRUE", "on", "ON", "yes", "YES"])
def test_opciones_aceptan_variantes_verdaderas(monkeypatch, valor):
    """Cada representación verdadera activa las tres opciones."""
    comprobar_opciones_configuradas(monkeypatch, valor, True)


@pytest.mark.parametrize("valor", ["0", "false", "False", "FALSE", "off", "OFF", "no", "NO"])
def test_opciones_aceptan_variantes_falsas(monkeypatch, valor):
    """Cada representación falsa desactiva las tres opciones."""
    comprobar_opciones_configuradas(monkeypatch, valor, False)


@pytest.mark.parametrize("valor", ["invalid", "2", "none", "", "   ", "maybe"])
def test_opciones_invalidas_recuperan_valores_predeterminados(monkeypatch, valor):
    """Una configuración inválida conserva los valores predeterminados."""
    comprobar_opciones_configuradas(monkeypatch, valor, True)
