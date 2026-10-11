"""Identidad de caché, exclusión voluntaria y expiración de respuestas de IA."""
from src.ai.openrouter_ai import OpenRouterIA
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_cache_conserva_respuestas_y_respeta_identidad_y_expiracion(monkeypatch):
    """La caché distingue opciones, contexto y vencimiento sin peticiones de más."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    current_time = 1000.0
    def mock_time():
        return current_time
    network_calls = 0
    def mock_post(url, headers=None, json=None, timeout=None):
        nonlocal network_calls
        network_calls += 1
        return RespuestaSimulada(200, {"choices": [{"message": {"content": f"Respuesta #{network_calls}"}}]})
    monkeypatch.setattr(OpenRouterIA, "_tiempo_monotonico", staticmethod(mock_time))
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res1 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res1.ok is True
    assert res1.cached is False
    assert network_calls == 1
    res2 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res2.ok is True
    assert res2.cached is True
    assert res2.text == res1.text
    assert network_calls == 1
    res3 = client.ask("¿Qué es un vector?", cacheable=True, simpler=True)
    assert res3.ok is True
    assert res3.cached is False
    assert network_calls == 2
    res4 = client.ask("¿Qué es un vector?", cacheable=True, context_block="[CONTEXTO]\n{\"v\":1}\n[/CONTEXTO]")
    assert res4.ok is True
    assert res4.cached is False
    assert network_calls == 3
    res5 = client.ask("¿Qué es un vector?", cacheable=False)
    assert res5.ok is True
    assert res5.cached is False
    assert network_calls == 4
    current_time += 3601.0
    res6 = client.ask("¿Qué es un vector?", cacheable=True)
    assert res6.ok is True
    assert res6.cached is False
    assert network_calls == 5
