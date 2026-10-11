"""Renderizado seguro de cuerpos LaTeX en contenedores MathJax."""
from __future__ import annotations

import html
import itertools
import json
from nicegui import ui

_CONTADOR_ID = itertools.count()


def render_latex(latex: str) -> None:
    """Inserta un bloque LaTeX desplazable y solicita su composición MathJax."""
    identificador = f"repro-math-{next(_CONTADOR_ID)}"
    contenido = html.escape(latex)
    ui.html(
        f'<div id="{identificador}" class="math-scroll-container math-label">$$ {contenido} $$</div>'
    )
    ui.run_javascript(
        f"if(window.scalaris && window.scalaris.renderizarMathJax) "
        f"window.scalaris.renderizarMathJax([{json.dumps(identificador)}]);"
    )
