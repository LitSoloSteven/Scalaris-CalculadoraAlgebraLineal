"""Regresiones de la cascada de modelos y del plazo compartido de Glosa."""
from types import SimpleNamespace

import pytest
import requests

from src.ai.cliente_openrouter import ClienteOpenRouter
from tests.comun_openrouter import RespuestaSimulada


PRIMARIO = "prueba/primario:free"
PRIMERA_RESERVA = "prueba/primera-reserva:free"
SEGUNDA_RESERVA = "prueba/segunda-reserva:free"


@pytest.fixture
def cliente(monkeypatch):
    """Configura una cascada que solo puede usar las respuestas simuladas."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    cliente = ClienteOpenRouter()
    cliente.MODELO_PRIMARIO = PRIMARIO
    cliente.MODELOS_RESERVA = [PRIMERA_RESERVA, SEGUNDA_RESERVA]
    monkeypatch.setattr(cliente, "_tiempo_dormir", lambda _: None)
    return cliente


def _respuesta_prueba():
    return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta útil"}}]})


@pytest.mark.parametrize("estado, datos", [
    (200, {"choices": [{"message": {"content": "   "}}]}),
    (200, {"error": {"code": 404}}),
    (200, {"choices": [{"error": {"code": 404}, "message": {"content": "Texto parcial"}}]}),
    (200, {"choices": [{"finish_reason": "error", "message": {"content": "Texto parcial"}}]}),
    (403, {"error": {"metadata": {"error_type": "permission_denied", "provider_code": "ineligible"}}}),
    (403, {"error": {"code": 403, "message": "This model is only available on agentic harnesses."}}),
    (404, {}),
])
def test_respuesta_inutil_o_rechazo_de_modelo_activa_reserva(cliente, monkeypatch, estado, datos):
    """Continúa ante respuestas vacías, fallos de generación e inelegibilidad del proveedor."""
    respuestas = iter([RespuestaSimulada(estado, datos), _respuesta_prueba()])
    monkeypatch.setattr(cliente, "_peticiones_post", lambda *_, **__: next(respuestas))

    resultado = cliente.preguntar("¿Qué es una matriz?")

    assert resultado.exito
    assert resultado.modelo == PRIMERA_RESERVA


def test_cascada_usa_todas_las_reservas_en_orden_sin_duplicar(cliente, monkeypatch):
    """El límite de la primera reserva permite consultar la siguiente."""
    cliente.MODELOS_RESERVA.insert(0, PRIMARIO)
    cliente.MODELOS_RESERVA.insert(2, PRIMERA_RESERVA)
    llamadas = []
    respuestas = iter([RespuestaSimulada(404), RespuestaSimulada(429), _respuesta_prueba()])

    def _responder(direccion, *, headers, json, timeout):
        llamadas.append(json["model"])
        return next(respuestas)

    monkeypatch.setattr(cliente, "_peticiones_post", _responder)
    resultado = cliente.preguntar("¿Qué es una matriz?")

    assert resultado.modelo == SEGUNDA_RESERVA
    assert llamadas == [PRIMARIO, PRIMERA_RESERVA, SEGUNDA_RESERVA]


@pytest.mark.parametrize("estado, metadatos", [
    (401, {}),
    (402, {}),
    (403, {"limit_source": "openrouter_key_limit"}),
    (403, {"patterns": ["texto filtrado"]}),
    (403, {"error_type": "content_policy_violation", "provider_code": "moderation"}),
])
def test_error_de_cuenta_o_politica_detiene_la_cascada(cliente, monkeypatch, estado, metadatos):
    """Conserva el rechazo terminal y evita enviar otra petición por la misma cuenta."""
    llamadas = []

    def _responder(*argumentos, **opciones):
        llamadas.append(opciones["json"]["model"])
        return RespuestaSimulada(estado, {"error": {"metadata": metadatos}})

    monkeypatch.setattr(cliente, "_peticiones_post", _responder)
    resultado = cliente.preguntar("¿Qué es una matriz?")

    assert not resultado.exito
    assert llamadas == [PRIMARIO]


def test_fin_por_filtro_del_proveedor_no_repite_la_consulta(cliente, monkeypatch):
    """Una generación filtrada se detiene incluso si viene dentro de HTTP 200."""
    respuestas = iter([RespuestaSimulada(200, {"choices": [{"finish_reason": "content_filter"}]})])
    monkeypatch.setattr(cliente, "_peticiones_post", lambda *_, **__: next(respuestas))

    assert not cliente.preguntar("¿Qué es una matriz?").exito


def test_reintento_y_timeout_dejan_tiempo_para_otras_reservas(cliente, monkeypatch):
    """Un primario lento y una reserva que agota su plazo dejan margen para la última."""
    reloj = SimpleNamespace(segundos=0.0)
    llamadas = []

    def _responder(direccion, *, headers, json, timeout):
        llamadas.append(json["model"])
        if len(llamadas) == 1:
            reloj.segundos += 11.0
            return RespuestaSimulada(503)
        if json["model"] == SEGUNDA_RESERVA:
            assert sum(timeout) == pytest.approx(10.0)
            return _respuesta_prueba()
        reloj.segundos += sum(timeout)
        raise requests.exceptions.ReadTimeout()

    monkeypatch.setattr(cliente, "_tiempo_monotonico", lambda: reloj.segundos)
    monkeypatch.setattr(cliente, "_tiempo_dormir", lambda segundos: setattr(reloj, "segundos", reloj.segundos + segundos))
    monkeypatch.setattr(cliente, "_peticiones_post", _responder)

    resultado = cliente.preguntar("¿Qué es una matriz?")

    assert resultado.exito and resultado.modelo == SEGUNDA_RESERVA
    assert llamadas == [PRIMARIO, PRIMARIO, PRIMERA_RESERVA, SEGUNDA_RESERVA]
