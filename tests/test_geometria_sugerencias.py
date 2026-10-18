"""Sugerencias específicas de las escenas geométricas."""
from src.frontend.sugerencias import Senales, generar_candidatas


def test_sugerencia_paralelismo_aparece_con_senal():
    """El estado sin solución y la señal de paralelismo ofrecen su sugerencia."""
    senales = Senales(herramienta="visualizador", estado="sin_solucion", banderas=frozenset({"paralelas"}))
    candidatas = generar_candidatas(senales)
    identificadores = [c.identificador for c in candidatas]
    assert "visualizador.paralelas" in identificadores


def test_sugerencia_paralelismo_ausente_sin_senal():
    """La sugerencia de paralelismo requiere su señal."""
    senales = Senales(herramienta="visualizador", estado="sin_solucion", banderas=frozenset())
    candidatas = generar_candidatas(senales)
    identificadores = [c.identificador for c in candidatas]
    assert "visualizador.paralelas" not in identificadores


def test_sugerencia_espacio_generado_aparece_con_resultado():
    """La escena de vectores ofrece una sugerencia sobre el espacio generado."""
    senales = Senales(herramienta="visualizador", estado="resultado", banderas=frozenset())
    candidatas = generar_candidatas(senales)
    identificadores = [c.identificador for c in candidatas]
    assert "visualizador.espacio_generado" in identificadores


def test_sugerencia_espacio_generado_ausente_sin_resultado():
    """El estado vacío no ofrece la sugerencia de espacio generado."""
    senales = Senales(herramienta="visualizador", estado="sin_resultado", banderas=frozenset())
    candidatas = generar_candidatas(senales)
    identificadores = [c.identificador for c in candidatas]
    assert "visualizador.espacio_generado" not in identificadores


def test_sugerencias_geometria_ausentes_en_otras_herramientas():
    """Las sugerencias geométricas solo corresponden al visualizador."""
    senales = Senales(herramienta="sistemas", estado="sin_solucion", banderas=frozenset({"paralelas"}))
    candidatas = generar_candidatas(senales)
    identificadores = [c.identificador for c in candidatas]
    assert "visualizador.paralelas" not in identificadores
    assert "visualizador.espacio_generado" not in identificadores
