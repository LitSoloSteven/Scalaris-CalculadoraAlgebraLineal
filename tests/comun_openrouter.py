"""Respuestas HTTP simuladas y aislamiento de caché del cliente OpenRouter."""
import json
import pytest

from src.ai.cliente_openrouter import ClienteOpenRouter


class RespuestaSimulada:
    """Respuesta mínima compatible con la API HTTP consumida por OpenRouter."""

    def __init__(self, status_code: int, datos_json: dict = None, text: str = ""):
        self.status_code = status_code
        self._datos_json = datos_json or {}
        self.text = text or json.dumps(self._datos_json)

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
