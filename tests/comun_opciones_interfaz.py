"""Preparación y verificación de las tres opciones configuradas por entorno."""
from src.frontend.banderas import navegacion_actualizada, panel_lateral_habilitado, proactivo_habilitado


def comprobar_opciones_configuradas(monkeypatch, valor, esperado):
    """Mantiene los mismos tres valores de entorno y exige cada resultado esperado."""
    monkeypatch.setenv('SCALARIS_NAV', valor)
    monkeypatch.setenv('SCALARIS_DOCK', valor)
    monkeypatch.setenv('SCALARIS_PROACTIVE', valor)
    assert navegacion_actualizada() is esperado
    assert panel_lateral_habilitado() is esperado
    assert proactivo_habilitado() is esperado
