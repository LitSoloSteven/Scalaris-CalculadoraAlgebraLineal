"""Ausencia de detalles internos en los mensajes de error de OpenRouter."""
import threading
import requests

from src.ai.openrouter_ai import OpenRouterIA
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_mensajes_error_no_revelan_detalles_internos(monkeypatch):
    """Los ocho tipos de error conservan mensajes sin datos técnicos sensibles."""
    prohibidas = ["Traceback", "Python", ".env", "OPENROUTER"]
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterIA()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    r_no_key = OpenRouterIA().ask("hola")
    cancel = threading.Event()
    cancel.set()
    r_cancelled = client.ask("hola", cancel=cancel)
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: RespuestaSimulada(401, text="Auth err")))
    r_auth = client.ask("hola")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: RespuestaSimulada(200, {"choices": []})))
    r_empty = client.ask("hola")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: RespuestaSimulada(429, text="Rate limit")))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    r_rate = client.ask("hola")
    def raise_timeout(*a, **k):
        raise requests.exceptions.Timeout("timeout")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(raise_timeout))
    r_timeout = client.ask("hola")
    def raise_conn(*a, **k):
        raise requests.exceptions.ConnectionError("conn")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(raise_conn))
    r_network = client.ask("hola")
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(lambda *a, **k: RespuestaSimulada(500, text="error")))
    r_service = client.ask("hola")
    todos_los_resultados = [r_no_key, r_cancelled, r_auth, r_empty, r_rate, r_timeout, r_network, r_service]
    for res in todos_los_resultados:
        for p in prohibidas:
            assert p not in res.text, f"Palabra prohibida '{p}' encontrada en: {res.text}"
