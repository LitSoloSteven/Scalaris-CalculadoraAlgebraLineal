"""Contratos estáticos de los activos del dock de Glosa.

INFERIDO: Estas pruebas verifican el contrato estático en los archivos de código (JS, Python, CSS),
no el comportamiento en un navegador en vivo.
"""
from pathlib import Path
import re
import pytest


def test_contrato_cliente_glosa():
    """Verifica contratos en glosa_dock.js."""
    js_path = Path("src/frontend/assets/js/glosa_dock.js")
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    assert "html.hasAttribute('data-glosa-instant')" in content
    instant_match = re.search(r"const instant\s*=\s*([^;]+);", content)
    assert instant_match is not None
    assert "html.hasAttribute('data-glosa-instant')" in instant_match.group(1)

    assert "documentElement.style.setProperty('--glosa-kb'" not in content

    assert "dock.style.setProperty('--glosa-kb', '0px')" in content


def test_contrato_accesibilidad_glosa():
    """Verifica contratos de accesibilidad en glosa_dock.py."""
    py_path = Path("src/frontend/componentes/glosa_dock.py")
    pie_path = Path("src/frontend/componentes/glosa_pie.py")
    assert py_path.exists() and pie_path.exists()
    content = py_path.read_text(encoding="utf-8") + "\n" + pie_path.read_text(encoding="utf-8")

    fab_match = re.search(r"classes\(['\"]glosa-fab['\"]\)\.props\(([^)]+)\)", content)
    assert fab_match is not None
    fab_props = fab_match.group(1)
    assert 'aria-controls="glosa-dock"' in fab_props
    assert 'aria-expanded="false"' in fab_props

    aside_match = re.search(r"ui\.element\(['\"]aside['\"]\)[^;]+?props\(([^)]+)\)", content)
    assert aside_match is not None
    aside_props = aside_match.group(1)
    assert "aria-expanded" not in aside_props


def test_contrato_css_dock_y_disposicion():
    """Verifica contratos en hojas CSS sobre FAB, transiciones del dock y tokens de layout."""
    from tests.comun import leer_css_completo
    content = leer_css_completo()

    assert 'html[data-glosa="open"] .glosa-fab' in content
    fab_open_css = content.split('html[data-glosa="open"] .glosa-fab')[1].split("}")[0]
    assert "visibility: hidden" in fab_open_css

    assert content.count("transform 200ms") >= 3
    assert content.count("visibility 0s linear 200ms") >= 3

    assert "100vh" not in content
    assert content.count("container-type: inline-size") == 3
    assert content.count("--fab-reserve:") >= 4
