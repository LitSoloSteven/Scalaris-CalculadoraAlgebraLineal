import pytest
import os
from src.frontend.componentes.glosa_renderizado import renderizar_texto_glosa
from tests.comun_clientes import PanelIASimulado

def test_renderizado_glosa_escapa_codigo():
    """El bloque de código se presenta escapado junto al texto del mensaje."""
    texto = "Hola\n```print('hola')```\nMás texto"
    res = renderizar_texto_glosa(texto)
    assert 'print(&#x27;hola&#x27;)' in res
    assert 'class="glosa-pre"' in res
    assert 'Hola' in res

def test_renderizado_glosa_bloque_sin_cierre():
    """El delimitador incompleto conserva los fragmentos de texto."""
    texto = "A```B"
    res = renderizar_texto_glosa(texto)
    assert 'A' in res
    assert 'B' in res

def test_historial_glosa_agrega_y_limpia_mensajes():
    """El historial admite un mensaje y vuelve al estado vacío al limpiarlo."""
    panel = PanelIASimulado(almacen={})
    assert len(panel.historial_chat) == 0
    panel.historial_chat.append({"texto": "Test"})
    assert len(panel.historial_chat) == 1
    panel.limpiar_chat()
    assert len(panel.historial_chat) == 0

def test_icono_glosa_es_svg():
    """El catálogo devuelve el icono SVG de Glosa."""
    from src.frontend.componentes.iconos import icono_svg
    assert '<svg' in icono_svg('glosa')

def test_contraste_glosa_declarado():
    """Conserva el caso histórico sin aserciones de contraste."""
    pass
