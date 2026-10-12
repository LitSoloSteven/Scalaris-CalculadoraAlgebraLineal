"""Opciones de interfaz configuradas mediante variables de entorno."""
import pytest
from src.frontend.flags import dock_enabled, nav_v2, proactive_enabled


def test_opciones_predeterminadas_sin_variables_de_entorno(monkeypatch):
    """Las opciones se activan cuando no hay configuración explícita."""
    monkeypatch.delenv("SCALARIS_NAV", raising=False)
    monkeypatch.delenv("SCALARIS_DOCK", raising=False)
    monkeypatch.delenv("SCALARIS_PROACTIVE", raising=False)
    assert nav_v2() is True
    assert dock_enabled() is True
    assert proactive_enabled() is True


@pytest.mark.parametrize("valor", ["1", "true", "True", "TRUE", "on", "ON", "yes", "YES"])
def test_opciones_aceptan_variantes_verdaderas(monkeypatch, valor):
    """Cada representación verdadera activa las tres opciones."""
    monkeypatch.setenv("SCALARIS_NAV", valor)
    monkeypatch.setenv("SCALARIS_DOCK", valor)
    monkeypatch.setenv("SCALARIS_PROACTIVE", valor)
    assert nav_v2() is True
    assert dock_enabled() is True
    assert proactive_enabled() is True


@pytest.mark.parametrize("valor", ["0", "false", "False", "FALSE", "off", "OFF", "no", "NO"])
def test_opciones_aceptan_variantes_falsas(monkeypatch, valor):
    """Cada representación falsa desactiva las tres opciones."""
    monkeypatch.setenv("SCALARIS_NAV", valor)
    monkeypatch.setenv("SCALARIS_DOCK", valor)
    monkeypatch.setenv("SCALARIS_PROACTIVE", valor)
    assert nav_v2() is False
    assert dock_enabled() is False
    assert proactive_enabled() is False


@pytest.mark.parametrize("valor", ["invalid", "2", "none", "", "   ", "maybe"])
def test_opciones_invalidas_recuperan_valores_predeterminados(monkeypatch, valor):
    """Una configuración inválida conserva los valores predeterminados."""
    monkeypatch.setenv("SCALARIS_NAV", valor)
    monkeypatch.setenv("SCALARIS_DOCK", valor)
    monkeypatch.setenv("SCALARIS_PROACTIVE", valor)
    assert nav_v2() is True
    assert dock_enabled() is True
    assert proactive_enabled() is True
