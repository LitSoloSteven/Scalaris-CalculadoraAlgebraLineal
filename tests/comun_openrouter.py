"""Respuestas HTTP simuladas y aislamiento de caché del cliente OpenRouter."""
import json
import pytest

from src.ai.openrouter_ai import OpenRouterIA


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
    import src.ai.openrouter_ai as modulo_openrouter
    with modulo_openrouter._bloqueo_cache:
        modulo_openrouter._cache_respuestas.clear()
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])
    yield
    with modulo_openrouter._bloqueo_cache:
        modulo_openrouter._cache_respuestas.clear()
