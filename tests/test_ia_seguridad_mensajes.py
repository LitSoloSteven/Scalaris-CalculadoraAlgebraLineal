"""Ausencia de detalles internos en los mensajes de error de OpenRouter."""
import threading
import requests

from src.ai.cliente_openrouter import ClienteOpenRouter
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


def test_mensajes_error_no_revelan_detalles_internos(monkeypatch):
    """Los ocho tipos de error conservan mensajes sin datos técnicos sensibles."""
    prohibidas = ["Traceback", "Python", ".env", "OPENROUTER"]
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    cliente = ClienteOpenRouter()
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    sin_clave = ClienteOpenRouter().preguntar("hola")
    cancelar = threading.Event()
    cancelar.set()
    cancelado = cliente.preguntar("hola", cancelar=cancelar)
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(lambda *argumentos, **opciones: RespuestaSimulada(401, text="Auth err")))
    autenticacion = cliente.preguntar("hola")
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(lambda *argumentos, **opciones: RespuestaSimulada(200, {"choices": []})))
    vacio = cliente.preguntar("hola")
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(lambda *argumentos, **opciones: RespuestaSimulada(429, text="Rate limit")))
    monkeypatch.setattr(ClienteOpenRouter, "_tiempo_dormir", staticmethod(lambda segundos: None))
    limite = cliente.preguntar("hola")
    def agotar_tiempo(*argumentos, **opciones):
        raise requests.exceptions.Timeout("timeout")
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(agotar_tiempo))
    tiempo_agotado = cliente.preguntar("hola")
    def fallar_conexion(*argumentos, **opciones):
        raise requests.exceptions.ConnectionError("conn")
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(fallar_conexion))
    red = cliente.preguntar("hola")
    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(lambda *argumentos, **opciones: RespuestaSimulada(500, text="error")))
    servicio = cliente.preguntar("hola")
    todos_los_resultados = [sin_clave, cancelado, autenticacion, vacio, limite, tiempo_agotado, red, servicio]
    for resultado in todos_los_resultados:
        for palabra in prohibidas:
            assert palabra not in resultado.texto, f"Palabra prohibida '{palabra}' encontrada en: {resultado.texto}"
