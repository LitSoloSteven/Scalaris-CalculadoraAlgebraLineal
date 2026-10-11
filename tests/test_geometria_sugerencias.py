"""Sugerencias específicas de las escenas geométricas."""
from src.frontend.suggestions import Signals, candidates


def test_sugerencia_paralelismo_aparece_con_senal():
    """El estado sin solución y la señal de paralelismo ofrecen su sugerencia."""
    signals = Signals(tool="visualizador", state="no_solution", flags=frozenset({"parallel"}))
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" in ids


def test_sugerencia_paralelismo_ausente_sin_senal():
    """La sugerencia de paralelismo requiere su señal."""
    signals = Signals(tool="visualizador", state="no_solution", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" not in ids


def test_sugerencia_espacio_generado_aparece_con_resultado():
    """La escena de vectores ofrece una sugerencia sobre el espacio generado."""
    signals = Signals(tool="visualizador", state="result", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.span" in ids


def test_sugerencia_espacio_generado_ausente_sin_resultado():
    """El estado vacío no ofrece la sugerencia de espacio generado."""
    signals = Signals(tool="visualizador", state="none", flags=frozenset())
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.span" not in ids


def test_sugerencias_geometria_ausentes_en_otras_herramientas():
    """Las sugerencias geométricas solo corresponden al visualizador."""
    signals = Signals(tool="sistemas", state="no_solution", flags=frozenset({"parallel"}))
    cands = candidates(signals)
    ids = [c.id for c in cands]
    assert "visualizador.parallel" not in ids
    assert "visualizador.span" not in ids
