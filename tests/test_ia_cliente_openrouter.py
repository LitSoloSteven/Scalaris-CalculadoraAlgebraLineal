import threading
import pytest
import requests

from src.ai.openrouter_ai import OpenRouterIA, AIResult, AIErrorKind
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_sin_clave_no_realiza_llamada_red(monkeypatch):
    """La clave ausente produce error de configuración sin petición HTTP."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return RespuestaSimulada(200)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("¿Qué es una matriz?")
    assert res.ok is False
    assert res.kind == AIErrorKind.NO_KEY
    assert call_count == 0


def test_respuesta_exitosa_con_contenido(monkeypatch):
    """Una respuesta HTTP exitosa conserva el texto del modelo."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append((url, json))
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Una matriz es un arreglo bidimensional."}}]})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Una matriz es un arreglo bidimensional."
    assert len(calls) == 1


def test_respuesta_exitosa_sin_opciones(monkeypatch):
    """Una respuesta sin opciones produce el error de contenido vacío."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def mock_post(url, headers=None, json=None, timeout=None):
        return RespuestaSimulada(200, {"choices": []})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.EMPTY


def test_error_autenticacion_sin_reintento(monkeypatch):
    """El rechazo de autenticación no reintenta la petición."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        return RespuestaSimulada(401, text="Unauthorized: invalid api key")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.AUTH
    assert len(calls) == 1


def test_limite_peticiones_primario_espera_y_reintenta(monkeypatch):
    """El primer límite de peticiones espera un segundo y reintenta."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    calls = []
    sleeps = []

    def mock_post(url, headers=None, json=None, timeout=None):
        calls.append(len(calls))
        if len(calls) == 1:
            return RespuestaSimulada(429, text="Rate limited")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta tras reintento"}}]})

    def mock_sleep(secs):
        sleeps.append(secs)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(mock_sleep))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Respuesta tras reintento"
    assert len(calls) == 2
    assert len(sleeps) == 1
    assert sleeps[0] == 1.0


def test_limite_persistente_usa_segundo_modelo(monkeypatch):
    """Tras dos rechazos del primario se consulta una vez el modelo de reserva."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    fallback_name = "backup/model-secondary:free"
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [fallback_name])
    calls = []
    sleeps = []

    def mock_post(url, headers=None, json=None, timeout=None):
        model_called = json.get("model")
        calls.append(model_called)
        if model_called != fallback_name:
            return RespuestaSimulada(429, text="Rate limit en modelo primario")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta desde fallback"}}]})

    def mock_sleep(secs):
        sleeps.append(secs)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(mock_sleep))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.text == "Respuesta desde fallback"
    assert res.model == fallback_name
    assert calls.count(OpenRouterIA.MODELO_PRIMARIO) == 2
    assert calls.count(fallback_name) == 1


def test_limite_peticiones_sin_modelo_reserva(monkeypatch):
    """Sin modelo de reserva se informa del límite de peticiones."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])

    def mock_post(url, headers=None, json=None, timeout=None):
        return RespuestaSimulada(429, text="Rate limit")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.RATE_LIMIT


def test_tiempo_agotado_con_y_sin_modelo_reserva(monkeypatch):
    """El tiempo agotado usa la reserva cuando existe y falla si no existe."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    fallback_name = "backup/model-timeout"
    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [fallback_name])

    def mock_post_with_fallback(url, headers=None, json=None, timeout=None):
        if json.get("model") == OpenRouterIA.MODELO_PRIMARIO:
            raise requests.exceptions.Timeout("Timeout en primario")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta exitosa en fallback"}}]})

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post_with_fallback))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is True
    assert res.model == fallback_name

    monkeypatch.setattr(OpenRouterIA, "MODELOS_RESERVA", [])

    def mock_post_timeout(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.Timeout("Timeout total")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post_timeout))
    client2 = OpenRouterIA()
    res2 = client2.ask("pregunta")
    assert res2.ok is False
    assert res2.kind == AIErrorKind.TIMEOUT


def test_error_conexion_informa_fallo_red(monkeypatch):
    """Una conexión fallida se clasifica como error de red."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def mock_post(url, headers=None, json=None, timeout=None):
        raise requests.exceptions.ConnectionError("Error de socket")

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.NETWORK


def test_cancelacion_previa_no_realiza_llamada(monkeypatch):
    """La cancelación previa produce su error sin petición HTTP."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    call_count = 0

    def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return RespuestaSimulada(200)

    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    client = OpenRouterIA()
    cancel = threading.Event()
    cancel.set()
    res = client.ask("pregunta", cancel=cancel)
    assert res.ok is False
    assert res.kind == AIErrorKind.CANCELLED
    assert call_count == 0


def test_plazo_agotado_con_reloj_simulado(monkeypatch):
    """El plazo casi agotado evita otro intento y produce error de servicio."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    simulated_time = 100.0

    def mock_time():
        return simulated_time

    def mock_post(url, headers=None, json=None, timeout=None):
        nonlocal simulated_time
        # La respuesta deja menos de dos segundos del plazo total.
        simulated_time = 139.5
        return RespuestaSimulada(500, text="Transient error")

    monkeypatch.setattr(OpenRouterIA, "_tiempo_monotonico", staticmethod(mock_time))
    monkeypatch.setattr(OpenRouterIA, "_peticiones_post", staticmethod(mock_post))
    monkeypatch.setattr(OpenRouterIA, "_tiempo_dormir", staticmethod(lambda s: None))
    client = OpenRouterIA()
    res = client.ask("pregunta")
    assert res.ok is False
    assert res.kind == AIErrorKind.SERVICE


