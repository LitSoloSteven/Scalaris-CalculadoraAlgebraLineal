"""Respuestas, reintentos, reserva y cancelación del cliente OpenRouter."""
import threading
import requests

from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.respuestas import TipoErrorIA
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter
from tests.comun_openrouter import consultar_con_respuestas_simuladas


def test_sin_clave_no_realiza_llamada_red(monkeypatch):
    """La clave ausente produce error de configuración sin petición HTTP."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    total_llamadas = 0

    def responder(*argumentos, **opciones):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        nonlocal total_llamadas
        total_llamadas += 1
        return RespuestaSimulada(200)

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("¿Qué es una matriz?")
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.SIN_CLAVE
    assert total_llamadas == 0


def test_respuesta_exitosa_con_contenido(monkeypatch):
    """Una respuesta HTTP exitosa conserva el texto del modelo."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    llamadas = []

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        llamadas.append((url, json))
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Una matriz es un arreglo bidimensional."}}]})

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("pregunta")
    assert resultado.exito is True
    assert resultado.texto == "Una matriz es un arreglo bidimensional."
    assert len(llamadas) == 1


def test_respuesta_exitosa_sin_opciones(monkeypatch):
    """Una respuesta sin opciones produce el error de contenido vacío."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        return RespuestaSimulada(200, {"choices": []})

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("pregunta")
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.VACIO


def test_error_autenticacion_sin_reintento(monkeypatch):
    """El rechazo de autenticación no reintenta la petición."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    llamadas = []

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        llamadas.append(url)
        return RespuestaSimulada(401, texto="Unauthorized: invalid api key")

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("pregunta")
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.AUTENTICACION
    assert len(llamadas) == 1


def test_limite_peticiones_primario_espera_y_reintenta(monkeypatch):
    """El primer límite de peticiones espera un segundo y reintenta."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    llamadas, esperas = [], []

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        llamadas.append(len(llamadas))
        if len(llamadas) == 1:
            return RespuestaSimulada(429, texto="Rate limited")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta tras reintento"}}]})

    def esperar(segundos):
        """Coordina la espera del escenario asíncrono de la prueba."""
        esperas.append(segundos)

    resultado = consultar_con_respuestas_simuladas(monkeypatch, responder, esperar, True)
    assert resultado.texto == "Respuesta tras reintento"
    assert len(llamadas) == 2
    assert len(esperas) == 1
    assert esperas[0] == 1.0


def test_limite_persistente_usa_segundo_modelo(monkeypatch):
    """Tras dos rechazos del primario se consulta una vez el modelo de reserva."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    nombre_reserva = "backup/model-secondary:free"
    monkeypatch.setattr(ClienteOpenRouter, "MODELOS_RESERVA", [nombre_reserva])
    llamadas, esperas = [], []

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        modelo_consultado = json.get("model")
        llamadas.append(modelo_consultado)
        if modelo_consultado != nombre_reserva:
            return RespuestaSimulada(429, texto="Rate limit en modelo primario")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta desde fallback"}}]})

    def esperar(segundos):
        """Coordina la espera del escenario asíncrono de la prueba."""
        esperas.append(segundos)

    resultado = consultar_con_respuestas_simuladas(monkeypatch, responder, esperar, True)
    assert resultado.texto == "Respuesta desde fallback"
    assert resultado.modelo == nombre_reserva
    assert llamadas.count(ClienteOpenRouter.MODELO_PRIMARIO) == 2
    assert llamadas.count(nombre_reserva) == 1


def test_limite_peticiones_sin_modelo_reserva(monkeypatch):
    """Sin modelo de reserva se informa del límite de peticiones."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(ClienteOpenRouter, "MODELOS_RESERVA", [])

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        return RespuestaSimulada(429, texto="Rate limit")

    resultado = consultar_con_respuestas_simuladas(monkeypatch, responder, lambda segundos: None, False)
    assert resultado.tipo_error == TipoErrorIA.LIMITE_PETICIONES


def test_tiempo_agotado_con_y_sin_modelo_reserva(monkeypatch):
    """El tiempo agotado usa la reserva cuando existe y falla si no existe."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    nombre_reserva = "backup/model-timeout"
    monkeypatch.setattr(ClienteOpenRouter, "MODELOS_RESERVA", [nombre_reserva])

    def responder_con_reserva(url, headers=None, json=None, timeout=None):
        """Procesa responder con reserva con los datos recibidos."""
        if json.get("model") == ClienteOpenRouter.MODELO_PRIMARIO:
            raise requests.exceptions.Timeout("Timeout en primario")
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta exitosa en fallback"}}]})

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder_con_reserva))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("pregunta")
    assert resultado.exito is True
    assert resultado.modelo == nombre_reserva
    monkeypatch.setattr(ClienteOpenRouter, "MODELOS_RESERVA", [])

    def agotar_tiempo(url, headers=None, json=None, timeout=None):
        """Procesa agotar tiempo con los datos recibidos."""
        raise requests.exceptions.Timeout("Timeout total")

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(agotar_tiempo))
    segundo_cliente = ClienteOpenRouter()
    segundo_resultado = segundo_cliente.preguntar("pregunta")
    assert segundo_resultado.exito is False
    assert segundo_resultado.tipo_error == TipoErrorIA.TIEMPO_AGOTADO


def test_error_conexion_informa_fallo_red(monkeypatch):
    """Una conexión fallida se clasifica como error de red."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fallar_conexion(url, headers=None, json=None, timeout=None):
        """Procesa fallar conexion con los datos recibidos."""
        raise requests.exceptions.ConnectionError("Error de socket")

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(fallar_conexion))
    cliente = ClienteOpenRouter()
    resultado = cliente.preguntar("pregunta")
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.RED


def test_cancelacion_previa_no_realiza_llamada(monkeypatch):
    """La cancelación previa produce su error sin petición HTTP."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    total_llamadas = 0

    def responder(*argumentos, **opciones):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        nonlocal total_llamadas
        total_llamadas += 1
        return RespuestaSimulada(200)

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    cancelar = threading.Event()
    cancelar.set()
    resultado = cliente.preguntar("pregunta", cancelar=cancelar)
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.CANCELADO
    assert total_llamadas == 0


def test_plazo_agotado_con_reloj_simulado(monkeypatch):
    """El plazo casi agotado evita otro intento y produce error de servicio."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    tiempo_simulado = 100.0

    def consultar_reloj():
        """Procesa consultar reloj con los datos recibidos."""
        return tiempo_simulado

    def responder(url, headers=None, json=None, timeout=None):
        """Devuelve la respuesta simulada para aislar la comunicación de red."""
        nonlocal tiempo_simulado
        # La respuesta deja menos de dos segundos del plazo total.
        tiempo_simulado = 139.5
        return RespuestaSimulada(500, texto="Transient error")

    monkeypatch.setattr(ClienteOpenRouter, "_tiempo_monotonico", staticmethod(consultar_reloj))
    resultado = consultar_con_respuestas_simuladas(monkeypatch, responder, lambda segundos: None, False)
    assert resultado.tipo_error == TipoErrorIA.SERVICIO


