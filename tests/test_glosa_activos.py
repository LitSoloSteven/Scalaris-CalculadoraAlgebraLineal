"""Contratos estáticos de los activos del panel lateral de Glosa."""
from pathlib import Path
import re
import pytest


def test_contrato_cliente_glosa():
    """Verifica contratos en glosa_panel_lateral.js."""
    ruta_javascript = Path("src/frontend/recursos/js/glosa_panel_lateral.js")
    assert ruta_javascript.exists()
    contenido = ruta_javascript.read_text(encoding="utf-8")

    assert "html.hasAttribute('data-glosa-instantaneo')" in contenido
    coincidencia_inmediata = re.search(r"const instantaneo\s*=\s*([^;]+);", contenido)
    assert coincidencia_inmediata is not None
    assert "html.hasAttribute('data-glosa-instantaneo')" in coincidencia_inmediata.group(1)

    assert "documentElement.style.setProperty('--glosa-kb'" not in contenido

    assert "panelLateral.style.setProperty('--glosa-kb', '0px')" in contenido


def test_contrato_accesibilidad_glosa():
    """Verifica contratos de accesibilidad en glosa_panel_lateral.py."""
    ruta_python = Path("src/frontend/componentes/glosa_panel_lateral.py")
    ruta_pie = Path("src/frontend/componentes/glosa_pie.py")
    assert ruta_python.exists() and ruta_pie.exists()
    contenido = ruta_python.read_text(encoding="utf-8") + "\n" + ruta_pie.read_text(encoding="utf-8")

    coincidencia_boton_flotante = re.search(r"classes\(['\"]glosa-boton-flotante['\"]\)\.props\(([^)]+)\)", contenido)
    assert coincidencia_boton_flotante is not None
    propiedades_boton_flotante = coincidencia_boton_flotante.group(1)
    assert 'aria-controls="glosa-panel-lateral"' in propiedades_boton_flotante
    assert 'aria-expanded="false"' in propiedades_boton_flotante

    coincidencia_panel_lateral = re.search(r"ui\.element\(['\"]aside['\"]\)[^;]+?props\(([^)]+)\)", contenido)
    assert coincidencia_panel_lateral is not None
    propiedades_panel_lateral = coincidencia_panel_lateral.group(1)
    assert "aria-expanded" not in propiedades_panel_lateral


def test_contrato_css_panel_lateral_y_disposicion():
    """Verifica contratos en hojas CSS sobre botón flotante, transiciones del panel lateral y tokens de disposición."""
    from tests.comun import leer_css_completo
    contenido = leer_css_completo()

    assert 'html[data-glosa="abierto"] .glosa-boton-flotante' in contenido
    css_boton_flotante_abierto = contenido.split('html[data-glosa="abierto"] .glosa-boton-flotante')[1].split("}")[0]
    assert "visibility: hidden" in css_boton_flotante_abierto

    panel = Path('src/frontend/recursos/css/vistas_glosa_panel_lateral.css').read_text(encoding='utf-8')
    transicion_panel = panel.split('.glosa-panel-lateral {', 1)[1].split('}', 1)[0]
    assert "transform var(--dur-view-exit) var(--ease-std)" in transicion_panel
    assert "visibility 0s var(--ease-std) var(--dur-view-exit)" in transicion_panel

    assert "100vh" not in contenido
    assert contenido.count("container-type: inline-size") == 4
    assert contenido.count("--fab-reserve:") >= 4
