"""Captura del HTML y las solicitudes MathJax producidas por el reproductor."""
from src.frontend.componentes.reproductor_pasos import cuerpos


def capturar_renderizado_latex(monkeypatch, latex):
    """Devuelve el bloque emitido y las solicitudes cliente sin montar una página."""
    html_renderizado, llamadas_javascript = [], []
    monkeypatch.setattr(cuerpos.ui, "html", html_renderizado.append)
    monkeypatch.setattr(cuerpos.ui, "run_javascript", llamadas_javascript.append)
    cuerpos.renderizar_latex(latex)
    return html_renderizado, llamadas_javascript
