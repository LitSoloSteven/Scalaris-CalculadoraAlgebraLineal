"""Identidad de caché, exclusión voluntaria y expiración de respuestas de IA."""
from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.respuestas import OpcionesConsulta
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_cache_conserva_respuestas_y_respeta_identidad_y_expiracion(monkeypatch):
    """La caché distingue opciones, contexto y vencimiento sin peticiones de más."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    tiempo_actual = 1000.0
    def _consultar_reloj():
        return tiempo_actual
    llamadas_red = 0
    def _responder(url, headers=None, json=None, timeout=None):
        nonlocal llamadas_red
        llamadas_red += 1
        return RespuestaSimulada(200, {"choices": [{"message": {"content": f"Respuesta #{llamadas_red}"}}]})
    monkeypatch.setattr(ClienteOpenRouter, "_tiempo_monotonico", staticmethod(_consultar_reloj))
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(_responder))
    cliente = ClienteOpenRouter()
    primero = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(usar_cache=True))
    assert primero.exito is True
    assert primero.desde_cache is False
    assert llamadas_red == 1
    segundo = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(usar_cache=True))
    assert segundo.exito is True
    assert segundo.desde_cache is True
    assert segundo.texto == primero.texto
    assert llamadas_red == 1
    tercero = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(True, True))
    assert tercero.exito is True
    assert tercero.desde_cache is False
    assert llamadas_red == 2
    cuarto = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(True), contexto="[CONTEXTO]\n{\"v\":1}\n[/CONTEXTO]")
    assert cuarto.exito is True
    assert cuarto.desde_cache is False
    assert llamadas_red == 3
    quinto = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(usar_cache=False))
    assert quinto.exito is True
    assert quinto.desde_cache is False
    assert llamadas_red == 4
    tiempo_actual += 3601.0
    sexto = cliente.preguntar("¿Qué es un vector?", opciones=OpcionesConsulta(usar_cache=True))
    assert sexto.exito is True
    assert sexto.desde_cache is False
    assert llamadas_red == 5
