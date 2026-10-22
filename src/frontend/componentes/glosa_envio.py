"""Flujo de envio, anti-rebote, temporizador de cancelacion e integracion con IA."""
from __future__ import annotations

import logging
import threading
import time
from nicegui import run, ui

from src.ai.respuestas import OpcionesConsulta, ResultadoIA, TipoErrorIA
from src.ai.textos import CONSULTA_CANCELADA, ERROR_SERVICIO, RESPUESTA_DEMASIADO_EXTENSA
from src.ai.presupuesto_mensajes import validar_longitud_mensaje
from src.frontend.componentes.glosa_preguntas import PreguntasGlosaMixin
from src.frontend.componentes.glosa_espera import iniciar_temporizador_cancelar, finalizar_envio
from src.frontend import banderas
from src.frontend.constantes import ANTI_REBOTE_GLOSA_SEGUNDOS
from src.frontend.componentes.historial_glosa import incorporar_mensaje
from src.frontend.textos import MENSAJE_ANTI_REBOTE_GLOSA

registro = logging.getLogger(__name__)


def _renderizar_indicador_escritura() -> ui.row:
    """Genera la burbuja visual del asistente con animacion de puntos suspensivos."""
    fila_escritura = ui.row().classes("w-full justify-start mb-0")
    with (
        fila_escritura,
        ui.column().classes("p-3 glosa-burbuja-asistente"),
    ):
        ui.html(
            '<div class="glosa-indicador-escritura" role="status" '
            'aria-label="Glosa esta escribiendo"><span>.</span><span>.</span><span>.</span></div>'
        )
    return fila_escritura


def _validar_mensaje_entrada(texto: str) -> bool:
    """Orienta ante mensajes excesivos antes de persistirlos o limpiar el campo."""
    try:
        validar_longitud_mensaje(texto)
    except ValueError as error:
        ui.notify(str(error), type="warning")
        return False
    return True


class EnvioGlosaMixin(PreguntasGlosaMixin):
    """Coordina la recepción de preguntas y su consulta asíncrona con antirrebote y bitácora."""

    async def enviar_mensaje(self) -> None:
        """Extrae el texto del campo de entrada y lanza el envio."""
        campo = getattr(self, "campo_entrada", None)
        texto = campo.value if campo else ""
        await self._enviar_mensaje_asincrono(texto)

    async def _enviar_consulta(
        self,
        texto: str,
        *,
        almacenable_en_cache: bool = False,
        mas_simple: bool = False,
        es_reintento: bool = False,
    ) -> None:
        """Coordina la validacion, llamada a la IA y renderizado de la respuesta."""
        if getattr(self, "_esta_enviando", False):
            return

        ahora = time.monotonic()
        if ahora - getattr(self, "_ultimo_envio", 0) < ANTI_REBOTE_GLOSA_SEGUNDOS:
            ui.notify(MENSAJE_ANTI_REBOTE_GLOSA, type="warning")
            return

        if not texto or not texto.strip():
            return
        if not _validar_mensaje_entrada(texto):
            return
        texto_limpio = texto.strip()

        fila_escritura, cancelar, identificador_solicitud = self._preparar_interfaz_envio(
            texto_limpio, almacenable_en_cache=almacenable_en_cache, mas_simple=mas_simple, es_reintento=es_reintento
        )
        indicadores = iniciar_temporizador_cancelar(self, identificador_solicitud, cancelar, fila_escritura)

        try:
            resultado = await self._consultar_motor_ia(texto_limpio, almacenable_en_cache, mas_simple, cancelar)
        finally:
            if self._contador_solicitudes == identificador_solicitud:
                finalizar_envio(self, indicadores)
        if self._contador_solicitudes == identificador_solicitud and resultado.tipo_error != TipoErrorIA.CANCELADO:
            self._procesar_resultado(resultado)

    def _preparar_interfaz_envio(
        self, texto: str, *, almacenable_en_cache: bool, mas_simple: bool, es_reintento: bool
    ) -> tuple[ui.row, threading.Event, int]:
        """Limpia el campo de entrada, registra el mensaje y crea el indicador de espera."""
        if getattr(self, "campo_entrada", None):
            self.campo_entrada.value = ""
            self.campo_entrada.disable()

        if not es_reintento:
            mensaje = {"texto": texto, "enviado": True, "almacenable_en_cache": almacenable_en_cache, "mas_simple": mas_simple}
            self.historial_chat = incorporar_mensaje(self.historial_chat, mensaje)

        self._esta_enviando = True
        self._ultimo_envio = time.monotonic()
        self._forzar_sugerencias = True
        self._renderizar_sugerencias_laterales()

        if hasattr(self, "contenedor_seguimientos") and self.contenedor_seguimientos:
            try:
                self.contenedor_seguimientos.delete()
                self.contenedor_seguimientos = None
            except Exception:
                pass

        with self.area_chat:
            if not es_reintento:
                self._dibujar_ultimo_mensaje()
            fila_escritura = _renderizar_indicador_escritura()
        self._desplazar_al_final()

        self._contador_solicitudes = getattr(self, "_contador_solicitudes", 0) + 1
        return fila_escritura, threading.Event(), self._contador_solicitudes

    def _dibujar_ultimo_mensaje(self) -> None:
        """Pinta el mensaje mas reciente del usuario en el area correspondiente."""
        if banderas.panel_lateral_habilitado():
            from src.frontend.componentes.glosa_bitacora import _renderizar_mensaje_lateral
            _renderizar_mensaje_lateral(self, self.historial_chat[-1], es_ultimo=False)
        elif hasattr(self, "_renderizar_mensaje"):
            self._renderizar_mensaje(self.historial_chat[-1], indice=len(self.historial_chat) - 1)

    async def _consultar_motor_ia(
        self, texto: str, usar_cache: bool, respuesta_simple: bool, cancelar: threading.Event
    ) -> ResultadoIA:
        """Invoca el motor de IA en hilo secundario para evitar bloquear el bucle de eventos."""
        contexto = self._recopilar_contexto()
        historial = self.historial_chat[:-1]
        try:
            resultado = await run.io_bound(
                self.motor_ia.preguntar,
                texto,
                historial=historial,
                contexto=contexto,
                cancelar=cancelar,
                opciones=OpcionesConsulta(usar_cache, respuesta_simple),
            )
            if resultado is None:
                return ResultadoIA(False, CONSULTA_CANCELADA, TipoErrorIA.CANCELADO)
            return resultado
        except Exception:
            registro.error("Error inesperado en consulta de Glosa")
            return ResultadoIA(False, ERROR_SERVICIO, tipo_error=TipoErrorIA.SERVICIO)

    def _procesar_resultado(self, resultado: ResultadoIA) -> None:
        """Inserta la respuesta exitosa o de error en la bitacora y la presenta."""
        try:
            validar_longitud_mensaje(resultado.texto)
        except ValueError:
            resultado = ResultadoIA(False, RESPUESTA_DEMASIADO_EXTENSA, TipoErrorIA.SERVICIO)
        if not resultado.exito:
            puede_reintentar = resultado.tipo_error not in (TipoErrorIA.SIN_CLAVE, TipoErrorIA.AUTENTICACION)
            mensaje = {"texto": resultado.texto, "enviado": False, "error": True, "reintentar": puede_reintentar}
        else:
            mensaje = {"texto": resultado.texto, "enviado": False, "error": False}

        self.historial_chat = incorporar_mensaje(self.historial_chat, mensaje)

        with self.area_chat:
            if banderas.panel_lateral_habilitado():
                from src.frontend.componentes.glosa_bitacora import _renderizar_mensaje_lateral
                _renderizar_mensaje_lateral(self, mensaje, es_ultimo=True)
            elif hasattr(self, "_renderizar_mensaje"):
                self._renderizar_mensaje(mensaje, indice=len(self.historial_chat) - 1)
        self._desplazar_al_final()
