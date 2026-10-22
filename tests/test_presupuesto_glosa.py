"""Presupuesto de preguntas, respuestas e historial antes de persistir o transmitir."""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.ai.clasificador_respuestas import procesar_respuesta_exitosa
from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.constantes import MAXIMO_CARACTERES_MENSAJE
from src.ai.historial import limpiar_historial_almacenado
from src.ai.mensajes import construir_mensajes, recortar_historial
from src.ai.respuestas import TipoErrorIA
from src.ai.textos import RESPUESTA_DEMASIADO_EXTENSA
from src.frontend.componentes.glosa_envio import EnvioGlosaMixin


def test_pregunta_excesiva_se_rechaza_antes_de_red_y_cache(monkeypatch):
    """La API directa tampoco transmite ni almacena preguntas excesivas."""
    cliente = ClienteOpenRouter()
    red = Mock(side_effect=AssertionError("No debe consultar el proveedor"))
    cache = Mock(side_effect=AssertionError("No debe consultar la caché"))
    monkeypatch.setattr(cliente, "_paso_cascada_modelos", red)
    monkeypatch.setattr(cliente, "_paso_cache", cache)
    resultado = cliente.preguntar("x" * (MAXIMO_CARACTERES_MENSAJE + 1))
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.ENTRADA_INVALIDA
    assert "Acorta" in resultado.texto
    red.assert_not_called()
    cache.assert_not_called()


def test_campo_e_historial_no_se_modifican_tras_rechazar_pregunta(monkeypatch):
    """El rechazo de servidor precede la preparación visual y conserva el texto editable."""
    texto = "x" * (MAXIMO_CARACTERES_MENSAJE + 1)
    preparar = Mock(side_effect=AssertionError("No debe iniciar un envío"))
    panel = SimpleNamespace(_preparar_interfaz_envio=preparar,
                            campo_entrada=SimpleNamespace(value=texto), historial_chat=[])
    aviso = Mock()
    monkeypatch.setattr("src.frontend.componentes.glosa_envio.ui.notify", aviso)
    asyncio.run(EnvioGlosaMixin._enviar_consulta(panel, texto))
    preparar.assert_not_called()
    assert panel.campo_entrada.value == texto
    assert panel.historial_chat == []
    assert "caracteres" in aviso.call_args.args[0]


@pytest.mark.parametrize("enviado", [False, True])
def test_historial_descarta_mensajes_excesivos_sin_mutar(enviado):
    """Ningún remitente puede introducir texto ilimitado en sesión o carga HTTP."""
    valido = {"texto": "texto completo", "enviado": enviado}
    excesivo = {"texto": "x" * (MAXIMO_CARACTERES_MENSAJE + 1), "enviado": enviado}
    historial = [valido, excesivo]
    assert limpiar_historial_almacenado(historial, 8) == [valido]
    assert recortar_historial(historial) == [{"role": "user" if enviado else "assistant", "content": "texto completo"}]
    assert historial == [valido, excesivo]
    assert limpiar_historial_almacenado(historial, 8)[0] is not valido


def test_frontera_de_pregunta_conserva_todos_los_caracteres():
    """El máximo inclusive no trunca ni reemplaza contenido admitido."""
    pregunta = "x" * MAXIMO_CARACTERES_MENSAJE
    assert construir_mensajes([], pregunta)[-1] == {"role": "user", "content": pregunta}
    with pytest.raises(ValueError, match="caracteres"):
        construir_mensajes([], pregunta + "x")


def test_respuesta_excesiva_no_se_guarda_como_exito():
    """El clasificador rechaza contenido grande antes de caché y persistencia."""
    respuesta = SimpleNamespace(json=lambda: {"choices": [{"message": {"content": "x" * (MAXIMO_CARACTERES_MENSAJE + 1)}}]})
    resultado = procesar_respuesta_exitosa(respuesta, "modelo")
    assert resultado.exito is False
    assert resultado.texto == RESPUESTA_DEMASIADO_EXTENSA
    assert resultado.tipo_error == TipoErrorIA.SERVICIO


@pytest.mark.parametrize("contenido", [["texto"], {"texto": "ajeno"}, 7, True])
def test_contenido_no_textual_del_proveedor_nunca_es_exito(contenido):
    """Un JSON válido con contenido ajeno al contrato no llega a caché o historial."""
    respuesta = SimpleNamespace(json=lambda: {"choices": [{"message": {"content": contenido}}]})
    resultado = procesar_respuesta_exitosa(respuesta, "modelo")
    assert resultado.exito is False
    assert resultado.tipo_error == TipoErrorIA.SERVICIO
    assert isinstance(resultado.texto, str)
