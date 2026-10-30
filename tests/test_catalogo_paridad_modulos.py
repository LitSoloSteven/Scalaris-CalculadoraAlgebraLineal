"""Catálogo contextual coherente de determinantes y modelos matriciales."""
import pytest

from src.ai.mensajes import construir_pregunta_explicar_paso
from src.frontend.catalogo_sugerencias import CATALOGO_SUGERENCIAS
from src.frontend.sugerencias import Senales, generar_candidatas


@pytest.mark.parametrize("herramienta", ["determinantes", "leontief", "transformaciones"])
def test_catalogo_identifica_la_herramienta_y_ambos_estados(herramienta):
    """Cada entrada nueva tiene identidad única y preguntas para captura y resultado."""
    entradas = [entrada for entrada in CATALOGO_SUGERENCIAS if entrada[0] == herramienta]
    assert entradas and all(entrada[2].startswith(herramienta + ".") for entrada in entradas)
    assert len({entrada[2] for entrada in entradas}) == len(entradas)
    for estado in ("sin_resultado", "exito"):
        assert generar_candidatas(Senales(herramienta, estado))


@pytest.mark.parametrize("tipo,fragmento", [("menor", "índices originales"), ("final", "resultado exacto")])
def test_glosa_tiene_instruccion_especifica_para_menor_y_final(tipo, fragmento):
    """La pregunta usa la instrucción pedagógica específica sin recalcular."""
    pregunta = construir_pregunta_explicar_paso(tipo, 1, 2, "Operación")
    assert fragmento in pregunta and "no recalcules" in pregunta
