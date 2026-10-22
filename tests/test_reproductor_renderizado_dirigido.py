"""Contrato de firmas cliente y destino exacto de la composición MathJax."""
import json
import re

from tests.comun import RAIZ
from tests.comun_renderizado import capturar_renderizado_latex


def test_mathjax_recibe_el_identificador_del_bloque_renderizado(monkeypatch):
    """La solicitud apunta al bloque nuevo y conserva la llamada con una lista de destinos."""
    bloques, llamadas = capturar_renderizado_latex(monkeypatch, "x < 1")
    identificador = re.search(r'id="(reproductor-matematicas-\d+)"', bloques[0]).group(1)
    assert llamadas == [f"if(window.scalaris && window.scalaris.renderizarMathJax) "
                        f"window.scalaris.renderizarMathJax([{json.dumps(identificador)}]);"]


def test_firmas_cliente_conservan_argumentos_para_revelar_y_destellar():
    """La publicación conserva dos argumentos de revelado y uno de destello."""
    codigo = (RAIZ / "src/frontend/recursos/js/reproductor_pasos.js").read_text(encoding="utf-8")
    assert re.search(r"\brevelar:\s*function\s*\(identificador,\s*texto\)", codigo)
    assert re.search(r"\bdestellar:\s*function\s*\(identificador\)", codigo)
