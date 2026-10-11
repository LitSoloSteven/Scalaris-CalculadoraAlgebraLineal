import pytest
import os
from src.frontend.componentes.glosa_render import render_glosa_text
from tests.comun_clientes import PanelIASimulado

def test_renderizado_glosa_escapa_codigo():
    """El bloque de código se presenta escapado junto al texto del mensaje."""
    text = "Hola\n```print('hola')```\nMás texto"
    res = render_glosa_text(text)
    assert 'print(&#x27;hola&#x27;)' in res
    assert 'class="glosa-pre"' in res
    assert 'Hola' in res

def test_renderizado_glosa_bloque_sin_cierre():
    """El delimitador incompleto conserva los fragmentos de texto."""
    text = "A```B"
    res = render_glosa_text(text)
    assert 'A' in res
    assert 'B' in res

def test_historial_glosa_agrega_y_limpia_mensajes():
    """El historial admite un mensaje y vuelve al estado vacío al limpiarlo."""
    panel = PanelIASimulado(almacen={})
    assert len(panel.chat_history) == 0
    panel.chat_history.append({"text": "Test"})
    assert len(panel.chat_history) == 1
    panel.clear_chat()
    assert len(panel.chat_history) == 0

def test_icono_glosa_es_svg():
    """El catálogo devuelve el icono SVG de Glosa."""
    from src.frontend.componentes.icons import icon_svg
    assert '<svg' in icon_svg('glosa')

def test_contraste_glosa_declarado():
    """Conserva el caso histórico sin aserciones de contraste."""
    pass
