"""Respuestas HTTP simuladas y aislamiento de caché del cliente OpenRouter."""
import json
import pytest

from src.ai.cliente_openrouter import ClienteOpenRouter


class RespuestaSimulada:
    """Respuesta mínima compatible con la API HTTP consumida por OpenRouter."""

    def __init__(self, status_code: int, datos_json: dict = None, texto: str = ""):
        self.status_code = status_code
        self._datos_json = datos_json or {}
        self.text = texto or json.dumps(self._datos_json)

    def json(self):
        """Devuelve el cuerpo de respuesta mediante la API de requests."""
        return self._datos_json


@pytest.fixture(autouse=True)
def limpiar_estado_openrouter(monkeypatch):
    """Aísla la caché y los modelos de reserva antes y después de cada caso."""
    import src.ai.cache_respuestas as modulo_cache
    with modulo_cache._bloqueo_cache:
        modulo_cache._cache_respuestas.clear()
    monkeypatch.setattr(ClienteOpenRouter, "MODELOS_RESERVA", [])
    yield
    with modulo_cache._bloqueo_cache:
        modulo_cache._cache_respuestas.clear()


def consultar_con_respuestas_simuladas(monkeypatch, responder, esperar, exito):
    """Instala las respuestas y esperas antes de exigir el estado de la misma pregunta."""
    monkeypatch.setattr(ClienteOpenRouter, '_peticiones_post', staticmethod(responder))
    monkeypatch.setattr(ClienteOpenRouter, '_tiempo_dormir', staticmethod(esperar))
    resultado = ClienteOpenRouter().preguntar('pregunta')
    assert resultado.exito is exito
    return resultado
