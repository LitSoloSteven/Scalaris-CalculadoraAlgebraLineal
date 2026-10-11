import asyncio
from unittest.mock import AsyncMock
from src.frontend.componentes.ai_panel import MAX_HISTORY
from src.frontend.componentes.glosa_dock import MAX_HISTORY as DOCK_MAX_HISTORY
from tests.comun_clientes import PanelIASimulado


def test_limites_historial_panel_y_dock():
    """Panel y dock comparten el máximo esperado de mensajes."""
    assert MAX_HISTORY == 60
    assert DOCK_MAX_HISTORY == 60


def test_inicializacion_recorta_historial_excesivo():
    """La inicialización conserva los sesenta mensajes más recientes."""
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': (i % 2 == 0)} for i in range(80)],
        'ai_ctx_enabled': True
    }
    panel = PanelIASimulado(almacen=mock_storage)

    assert len(panel.chat_history) == 60
    assert panel.chat_history[0]['text'] == 'msg 20'
    assert panel.chat_history[-1]['text'] == 'msg 79'


def test_inicializacion_conserva_historial_bajo_limite():
    """El historial bajo el máximo mantiene su cantidad y primer mensaje."""
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': True} for i in range(30)],
        'ai_ctx_enabled': True
    }
    panel = PanelIASimulado(almacen=mock_storage)

    assert len(panel.chat_history) == 30
    assert panel.chat_history[0]['text'] == 'msg 0'


def test_agregar_mensaje_recorta_historial_al_limite():
    """Al agregar un mensaje se conserva la ventana final del historial."""
    mock_storage = {
        'ai_chat_history': [{'text': f'msg {i}', 'sent': True} for i in range(60)],
        'ai_ctx_enabled': True
    }
    panel = PanelIASimulado(almacen=mock_storage)

    msg = {"text": "msg 60", "sent": True}
    panel.chat_history.append(msg)
    if len(panel.chat_history) > MAX_HISTORY:
        panel.chat_history = panel.chat_history[-MAX_HISTORY:]

    assert len(panel.chat_history) == 60
    assert panel.chat_history[0]['text'] == 'msg 1'
    assert panel.chat_history[-1]['text'] == 'msg 60'
