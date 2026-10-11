"""Los registros de IA no incorporan cuerpos ni excepciones externos."""
import logging
import pytest
import requests

from src.ai.openrouter_ai import OpenRouterIA
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


@pytest.mark.parametrize("codigo", [401, 403, 500, 418])
def test_registro_http_omite_cuerpo_privado_y_caracteres_control(monkeypatch, caplog, codigo):
    """El diagnóstico conserva el estado HTTP sin reproducir datos del proveedor."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    secreto = "secreto-ficticio\nregistro-inyectado"

    def responder(url, headers=None, json=None, timeout=None):
        return RespuestaSimulada(codigo, text=secreto)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(responder))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda _: None))
    with caplog.at_level(logging.WARNING):
        OpenRouterIA().ask("Consulta")
    assert str(codigo) in caplog.text
    assert "secreto-ficticio" not in caplog.text
    assert "registro-inyectado" not in caplog.text


def test_registro_red_omite_detalles_de_excepcion(monkeypatch, caplog):
    """Las excepciones de transporte no se copian al registro del servidor."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")

    def fallar(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.RequestException("secreto-ficticio\nregistro-inyectado")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(fallar))
    with caplog.at_level(logging.ERROR):
        respuesta = OpenRouterIA().ask("Consulta")
    assert not respuesta.ok
    assert caplog.records
    assert "secreto-ficticio" not in caplog.text
    assert "registro-inyectado" not in caplog.text
