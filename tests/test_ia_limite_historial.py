import asyncio
from unittest.mock import AsyncMock
from unittest.mock import Mock
import pytest
from nicegui import ui
from src.ai.respuestas import ResultadoIA
from src.frontend.constantes import MAXIMO_HISTORIAL
from src.frontend import banderas
from src.frontend.componentes import glosa_bitacora
from tests.comun_clientes import PanelIASimulado


@pytest.mark.parametrize("panel_lateral", [False, True])
def test_limites_historial_panel_y_panel_lateral(monkeypatch, panel_lateral):
    """Ambas modalidades conservan sesenta mensajes al iniciar, preguntar y responder."""
    assert MAXIMO_HISTORIAL == 60
    monkeypatch.setattr(banderas, "panel_lateral_habilitado", lambda: panel_lateral)
    monkeypatch.setattr(glosa_bitacora, "_renderizar_mensaje_lateral", Mock())
    almacen = {'ia_historial_chat': [
        {'texto': f'msg {indice}', 'enviado': True} for indice in range(80)
    ]}
    panel = PanelIASimulado(almacen=almacen)
    panel.area_chat = ui.column()
    panel._renderizar_sugerencias_laterales = Mock()
    panel._renderizar_mensaje = Mock()
    panel._desplazar_al_final = Mock()
    try:
        assert len(panel.historial_chat) == 60
        assert panel.historial_chat[0]['texto'] == 'msg 20'
        panel._preparar_interfaz_envio(
            'pregunta', almacenable_en_cache=False, mas_simple=False, es_reintento=False
        )
        assert len(panel.historial_chat) == 60
        assert panel.historial_chat[0]['texto'] == 'msg 21'
        assert panel.historial_chat[-1]['texto'] == 'pregunta'
        panel._procesar_resultado(ResultadoIA(True, 'respuesta'))
        assert len(panel.historial_chat) == 60
        assert panel.historial_chat[0]['texto'] == 'msg 22'
        assert panel.historial_chat[-1]['texto'] == 'respuesta'
    finally:
        panel.area_chat.delete()


def test_inicializacion_recorta_historial_excesivo():
    """La inicialización conserva los sesenta mensajes más recientes."""
    almacen_simulado = {
        'ia_historial_chat': [{'texto': f'msg {i}', 'enviado': (i % 2 == 0)} for i in range(80)],
        'ia_contexto_habilitado': True
    }
    panel = PanelIASimulado(almacen=almacen_simulado)

    assert len(panel.historial_chat) == 60
    assert panel.historial_chat[0]['texto'] == 'msg 20'
    assert panel.historial_chat[-1]['texto'] == 'msg 79'


def test_inicializacion_conserva_historial_bajo_limite():
    """El historial bajo el máximo mantiene su cantidad y primer mensaje."""
    almacen_simulado = {
        'ia_historial_chat': [{'texto': f'msg {i}', 'enviado': True} for i in range(30)],
        'ia_contexto_habilitado': True
    }
    panel = PanelIASimulado(almacen=almacen_simulado)

    assert len(panel.historial_chat) == 30
    assert panel.historial_chat[0]['texto'] == 'msg 0'


def test_agregar_mensaje_recorta_historial_al_limite():
    """Al agregar un mensaje se conserva la ventana final del historial."""
    almacen_simulado = {
        'ia_historial_chat': [{'texto': f'msg {i}', 'enviado': True} for i in range(60)],
        'ia_contexto_habilitado': True
    }
    panel = PanelIASimulado(almacen=almacen_simulado)

    mensaje = {"texto": "msg 60", "enviado": True}
    panel.historial_chat.append(mensaje)
    if len(panel.historial_chat) > MAXIMO_HISTORIAL:
        panel.historial_chat = panel.historial_chat[-MAXIMO_HISTORIAL:]

    assert len(panel.historial_chat) == 60
    assert panel.historial_chat[0]['texto'] == 'msg 1'
    assert panel.historial_chat[-1]['texto'] == 'msg 60'
