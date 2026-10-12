"""Contrato español de consultas y puente del panel hacia OpenRouter."""
import asyncio
from dataclasses import FrozenInstanceError, asdict
import inspect
import logging
import threading
from types import SimpleNamespace

import pytest

from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.mensajes import SUFIJO_MAS_SIMPLE
from src.ai.respuestas import OpcionesConsulta, ResultadoIA, TipoErrorIA
from src.ai.textos import CONSULTA_CANCELADA, ERROR_SERVICIO
from src.frontend.componentes import glosa_envio
from tests.comun_openrouter import RespuestaSimulada, limpiar_estado_openrouter


@pytest.mark.parametrize("usar_cache", [False, True])
@pytest.mark.parametrize("respuesta_simple", [False, True])
def test_opciones_conservan_payload_y_reutilizacion(monkeypatch, usar_cache, respuesta_simple):
    """Las cuatro combinaciones conservan el mensaje efectivo y la política de caché."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    peticiones = []

    def responder(url, headers=None, json=None, timeout=None):
        peticiones.append((headers, json, timeout))
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Respuesta"}}]})

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    opciones = OpcionesConsulta(usar_cache, respuesta_simple)
    primero = cliente.preguntar("Pregunta", contexto="Contexto", opciones=opciones)
    segundo = cliente.preguntar("Pregunta", contexto="Contexto", opciones=opciones)
    cabeceras, datos, tiempos = peticiones[0]
    sufijo = SUFIJO_MAS_SIMPLE if respuesta_simple else ""
    assert datos["messages"][-1] == {
        "role": "user", "content": f"Contexto\n\nPregunta del estudiante: Pregunta{sufijo}",
    }
    assert set(datos) == {"model", "messages"}
    assert cabeceras["Authorization"] == "Bearer clave-ficticia"
    assert tiempos[0] <= 5.0 and tiempos[1] <= 25.0
    assert primero.modelo == datos["model"]
    assert not primero.desde_cache
    assert segundo.desde_cache is usar_cache
    assert len(peticiones) == (1 if usar_cache else 2)


def test_resultado_y_opciones_son_inmutables_y_sin_alias():
    """Los datos internos solo exponen sus campos españoles y no permiten mutación."""
    resultado = ResultadoIA(True, "Respuesta", modelo="modelo")
    opciones = OpcionesConsulta()
    assert asdict(resultado) == {
        "exito": True, "texto": "Respuesta", "tipo_error": None,
        "modelo": "modelo", "desde_cache": False,
    }
    assert asdict(opciones) == {"usar_cache": False, "respuesta_simple": False}
    with pytest.raises(FrozenInstanceError):
        resultado.texto = "Otro texto"
    with pytest.raises(FrozenInstanceError):
        opciones.usar_cache = True
    assert not any(hasattr(resultado, nombre) for nombre in ("ok", "text", "kind", "model", "cached"))
    assert not hasattr(ClienteOpenRouter, "ask")
    assert list(inspect.signature(ClienteOpenRouter().preguntar).parameters) == [
        "pregunta", "historial", "contexto", "cancelar", "opciones",
    ]


def test_cancelacion_durante_http_no_guarda_respuesta(monkeypatch):
    """Una cancelación durante el transporte descarta el texto sin guardarlo en caché."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "clave-ficticia")
    cancelar = threading.Event()
    llamadas = []

    def responder(url, headers=None, json=None, timeout=None):
        llamadas.append(json)
        cancelar.set()
        return RespuestaSimulada(200, {"choices": [{"message": {"content": "Descartada"}}]})

    monkeypatch.setattr(ClienteOpenRouter, "_peticiones_post", staticmethod(responder))
    cliente = ClienteOpenRouter()
    opciones = OpcionesConsulta(usar_cache=True)
    primero = cliente.preguntar("Pregunta", cancelar=cancelar, opciones=opciones)
    cancelar.clear()
    segundo = cliente.preguntar("Pregunta", cancelar=cancelar, opciones=opciones)
    assert primero.tipo_error == segundo.tipo_error == TipoErrorIA.CANCELADO
    assert len(llamadas) == 2
    assert not primero.desde_cache and not segundo.desde_cache


@pytest.mark.parametrize("usar_cache", [False, True])
@pytest.mark.parametrize("respuesta_simple", [False, True])
def test_panel_transmite_historial_contexto_y_opciones(monkeypatch, usar_cache, respuesta_simple):
    """El puente transmite los datos al cliente real sin incluir la pregunta dos veces."""
    esperado = ResultadoIA(True, "Respuesta")
    peticiones = []
    historial = [{"text": "Anterior", "sent": True}, {"text": "Pregunta", "sent": True}]
    cancelar = threading.Event()

    def preguntar(pregunta, historial=None, contexto=None, cancelar=None, opciones=None):
        peticiones.append((pregunta, historial, contexto, cancelar, opciones))
        return esperado

    async def ejecutar(funcion, *argumentos, **opciones):
        return funcion(*argumentos, **opciones)

    monkeypatch.setattr(glosa_envio.run, "io_bound", ejecutar)
    panel = SimpleNamespace(
        motor_ia=SimpleNamespace(preguntar=preguntar), chat_history=historial,
        _collect_context=lambda: "Contexto",
    )
    obtenido = asyncio.run(glosa_envio.EnvioGlosaMixin._consultar_motor_ia(
        panel, "Pregunta", usar_cache, respuesta_simple, cancelar,
    ))
    assert obtenido is esperado
    assert peticiones == [(
        "Pregunta", historial[:-1], "Contexto", cancelar,
        OpcionesConsulta(usar_cache, respuesta_simple),
    )]


def test_error_inesperado_del_puente_omite_detalles_privados(monkeypatch, caplog):
    """El fallo imprevisto devuelve un mensaje genérico sin registrar datos sensibles."""
    async def fallar(*argumentos, **opciones):
        raise RuntimeError("secreto-ficticio\nregistro-inyectado")

    monkeypatch.setattr(glosa_envio.run, "io_bound", fallar)
    panel = SimpleNamespace(
        motor_ia=SimpleNamespace(preguntar=lambda pregunta: None),
        chat_history=[], _collect_context=lambda: "",
    )
    with caplog.at_level(logging.ERROR):
        resultado = asyncio.run(glosa_envio.EnvioGlosaMixin._consultar_motor_ia(
            panel, "Pregunta", False, False, threading.Event(),
        ))
    assert resultado == ResultadoIA(False, ERROR_SERVICIO, TipoErrorIA.SERVICIO)
    assert caplog.records
    assert "secreto-ficticio" not in caplog.text
    assert "registro-inyectado" not in caplog.text


def test_trabajador_cancelado_devuelve_resultado_cancelado(monkeypatch):
    """La ausencia de resultado por cancelación o apagado conserva un contrato válido."""
    async def terminar_sin_resultado(*argumentos, **opciones):
        return None

    monkeypatch.setattr(glosa_envio.run, "io_bound", terminar_sin_resultado)
    panel = SimpleNamespace(
        motor_ia=SimpleNamespace(preguntar=lambda pregunta: None),
        chat_history=[], _collect_context=lambda: "",
    )
    resultado = asyncio.run(glosa_envio.EnvioGlosaMixin._consultar_motor_ia(
        panel, "Pregunta", False, False, threading.Event(),
    ))
    assert resultado == ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO)
