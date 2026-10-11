"""Flujo de envio, anti-rebote, temporizador de cancelacion e integracion con IA."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any
from nicegui import run, ui

from src.ai.openrouter_ai import AIErrorKind, AIResult
from src.ai.prompts import construir_pregunta_explicar_paso
from src.frontend import flags
from src.frontend.constantes import ANTI_REBOTE_GLOSA_SEGUNDOS, MAX_HISTORIAL
from src.frontend.textos import MSJ_ANTI_REBOTE_GLOSA

logger = logging.getLogger(__name__)
MAX_HISTORY = MAX_HISTORIAL


def _renderizar_indicador_escritura() -> ui.row:
    """Genera la burbuja visual del asistente con animacion de puntos suspensivos."""
    fila_escritura = ui.row().classes("w-full justify-start mb-0")
    with fila_escritura:
        with ui.column().classes("p-3 glosa-burbuja-asistente"):
            ui.html(
                '<div class="glosa-typing-indicator" role="status" '
                'aria-label="Glosa esta escribiendo"><span>.</span><span>.</span><span>.</span></div>'
            )
    return fila_escritura


def iniciar_temporizador_cancelar(
    instancia: Any, req_id: int, cancel_event: threading.Event, fila_escritura: ui.row
) -> ui.row | None:
    """Programa la aparicion del boton cancelar si la peticion excede 5 segundos."""
    cancel_btn_row: list[ui.row | None] = [None]

    async def _mostrar_cancelar():
        await asyncio.sleep(5)
        if instancia._request_counter == req_id and getattr(instancia, "_is_sending", False) and not cancel_event.is_set():
            with instancia.chat_area:
                cancel_btn_row[0] = ui.row().classes("w-full justify-center mt-2")
                with cancel_btn_row[0]:
                    ui.button("Cancelar", on_click=_cancelar_peticion).classes(
                        "btn-ghost text-xs text-sec"
                    )
            instancia._scroll_to_bottom()

    def _cancelar_peticion():
        if instancia._request_counter == req_id and getattr(instancia, "_is_sending", False):
            cancel_event.set()
            instancia._request_counter += 1
            finalizar_envio(instancia, fila_escritura, cancel_btn_row[0])
            instancia._last_send_time = 0.0

    with instancia.chat_area:
        ui.timer(0, _mostrar_cancelar, once=True)
    return cancel_btn_row[0]


def finalizar_envio(instancia: Any, typing_row: ui.row | None, cancel_btn_row: ui.row | None) -> None:
    """Restablece los controles y limpia indicadores temporales de espera."""
    try:
        if typing_row:
            typing_row.delete()
    except Exception:
        pass
    try:
        if cancel_btn_row:
            cancel_btn_row.delete()
    except Exception:
        pass
    instancia._is_sending = False
    campo = getattr(instancia, "input_field", None)
    if campo:
        campo.enable()
    instancia._force_chips_render = True
    instancia._render_dock_chips()


class EnvioGlosaMixin:
    """Maneja la recepcion de preguntas, anti-rebote, consulta async y bitacora."""

    async def send_message_dock(self) -> None:
        """Extrae el texto del campo de entrada y lanza el envio."""
        campo = getattr(self, "input_field", None)
        texto = campo.value if campo else ""
        await self._submit(texto)

    def ask_suggestion(self, sugerencia: Any, from_keyboard: bool = False) -> None:
        """Procesa el clic o seleccion de teclado de un chip de sugerencia."""
        if getattr(self, "_is_sending", False):
            ui.notify("Glosa esta respondiendo. Espera a que termine.", type="warning")
            return

        if sugerencia.focus and hasattr(self.active_ui, "focus_cell"):
            self.active_ui.focus_cell(sugerencia.focus)

        if flags.dock_enabled() and not getattr(self, "is_open", False):
            cmd = "window.scalaris?.glosa?.abrir({instant: true, trigger: 'keyboard'});" if from_keyboard else "window.scalaris?.glosa?.abrir();"
            ui.run_javascript(f"if(window.scalaris && window.scalaris.glosa) {cmd}")

        if from_keyboard and getattr(self, "input_field", None) and not sugerencia.focus:
            ui.run_javascript("setTimeout(() => { const el = document.querySelector('.glosa-input textarea'); if(el) el.focus(); }, 100);")

        self._spawn(self._submit(sugerencia.text, cacheable=True, from_keyboard=from_keyboard))

    def ask_followup(self, seguimiento: Any, from_keyboard: bool = False) -> None:
        """Envia una pregunta de seguimiento seleccionada por el usuario."""
        if getattr(self, "_is_sending", False):
            ui.notify("Glosa esta respondiendo. Espera a que termine.", type="warning")
            return

        if from_keyboard and getattr(self, "input_field", None):
            ui.run_javascript("setTimeout(() => { const el = document.querySelector('.glosa-input textarea'); if(el) el.focus(); }, 100);")

        self._spawn(self._submit(seguimiento.question, cacheable=False, simpler=seguimiento.simpler, from_keyboard=from_keyboard))

    def disparar_explicacion_paso(self, meta_paso: dict[str, Any]) -> None:
        """Inicia la explicacion didactica de un paso procedimental."""
        if getattr(self, "_is_sending", False):
            ui.notify("Glosa esta respondiendo. Espera a que termine.", type="warning")
            return

        if flags.dock_enabled() and not getattr(self, "is_open", False):
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.abrir();")

        if hasattr(self, "set_explain_focus"):
            self.set_explain_focus(meta_paso)

        pregunta = construir_pregunta_explicar_paso(
            meta_paso.get("kind", "otro"),
            meta_paso.get("index", 1),
            meta_paso.get("total", 1),
            meta_paso.get("op", ""),
        )
        self._spawn(self._submit(pregunta, cacheable=True, simpler=True))

    def _retry_last_dock(self) -> None:
        """Reintenta el ultimo mensaje enviado tras un fallo recuperable."""
        ultimo_usuario = next((m for m in reversed(self.chat_history) if m.get("sent")), None)
        if self.chat_history and self.chat_history[-1].get("error"):
            self.chat_history.pop()

        self.render_chat_dock()
        if ultimo_usuario:
            self._spawn(self._submit(
                ultimo_usuario.get("text", ""),
                cacheable=ultimo_usuario.get("cacheable", False),
                simpler=ultimo_usuario.get("simpler", False),
                is_retry=True,
            ))

    async def _submit(
        self,
        text: str,
        *,
        cacheable: bool = False,
        simpler: bool = False,
        from_keyboard: bool = False,
        is_retry: bool = False,
    ) -> None:
        """Coordina la validacion, llamada a la IA y renderizado de la respuesta."""
        if getattr(self, "_is_sending", False):
            return

        ahora = time.monotonic()
        if ahora - getattr(self, "_last_send_time", 0) < ANTI_REBOTE_GLOSA_SEGUNDOS:
            ui.notify(MSJ_ANTI_REBOTE_GLOSA, type="warning")
            return

        if not text or not text.strip():
            return
        texto_limpio = text.strip()

        fila_escritura, cancel_event, req_id = self._preparar_interfaz_envio(
            texto_limpio, cacheable=cacheable, simpler=simpler, is_retry=is_retry
        )
        cancel_btn_row = iniciar_temporizador_cancelar(self, req_id, cancel_event, fila_escritura)

        resultado = await self._consultar_motor_ia(texto_limpio, cacheable, simpler, cancel_event)
        if self._request_counter == req_id:
            finalizar_envio(self, fila_escritura, cancel_btn_row)
            if resultado.kind != AIErrorKind.CANCELLED:
                self._procesar_resultado(resultado)

    def _preparar_interfaz_envio(
        self, texto: str, *, cacheable: bool, simpler: bool, is_retry: bool
    ) -> tuple[ui.row, threading.Event, int]:
        """Limpia el campo de entrada, registra el mensaje y crea el indicador de espera."""
        if getattr(self, "input_field", None):
            self.input_field.value = ""
            self.input_field.disable()

        if not is_retry:
            self.chat_history.append({"text": texto, "sent": True, "cacheable": cacheable, "simpler": simpler})
            if len(self.chat_history) > MAX_HISTORY:
                self.chat_history = self.chat_history[-MAX_HISTORY:]

        self._is_sending = True
        self._last_send_time = time.monotonic()
        self._force_chips_render = True
        self._render_dock_chips()

        if hasattr(self, "followups_container") and self.followups_container:
            try:
                self.followups_container.delete()
                self.followups_container = None
            except Exception:
                pass

        with self.chat_area:
            if not is_retry:
                self._dibujar_ultimo_mensaje()
            fila_escritura = _renderizar_indicador_escritura()
        self._scroll_to_bottom()

        self._request_counter = getattr(self, "_request_counter", 0) + 1
        return fila_escritura, threading.Event(), self._request_counter

    def _dibujar_ultimo_mensaje(self) -> None:
        """Pinta el mensaje mas reciente del usuario en el area correspondiente."""
        if flags.dock_enabled():
            from src.frontend.componentes.glosa_bitacora import _renderizar_mensaje_dock
            _renderizar_mensaje_dock(self, self.chat_history[-1], is_last=False)
        elif hasattr(self, "_render_message"):
            self._render_message(self.chat_history[-1], idx=len(self.chat_history) - 1)

    async def _consultar_motor_ia(
        self, texto: str, cacheable: bool, simpler: bool, cancel_event: threading.Event
    ) -> AIResult:
        """Invoca el motor de IA en hilo secundario para evitar bloquear el bucle de eventos."""
        ctx_block = self._collect_context()
        historial = self.chat_history[:-1]
        try:
            return await run.io_bound(
                self.motor_ia.ask,
                texto,
                history=historial,
                context_block=ctx_block,
                cancel=cancel_event,
                cacheable=cacheable,
                simpler=simpler,
            )
        except Exception:
            logger.exception("Error inesperado en consulta de Glosa")
            return AIResult(
                False,
                "Glosa no pudo responder ahora. Vuelve a intentarlo en un momento.",
                kind=AIErrorKind.SERVICE,
            )

    def _procesar_resultado(self, resultado: AIResult) -> None:
        """Inserta la respuesta exitosa o de error en la bitacora y la presenta."""
        if not resultado.ok:
            puede_reintentar = resultado.kind not in (AIErrorKind.NO_KEY, AIErrorKind.AUTH)
            msg = {"text": resultado.text, "sent": False, "error": True, "retry": puede_reintentar}
        else:
            msg = {"text": resultado.text, "sent": False, "error": False}

        self.chat_history.append(msg)
        if len(self.chat_history) > MAX_HISTORY:
            self.chat_history = self.chat_history[-MAX_HISTORY:]

        with self.chat_area:
            if flags.dock_enabled():
                from src.frontend.componentes.glosa_bitacora import _renderizar_mensaje_dock
                _renderizar_mensaje_dock(self, msg, is_last=True)
            elif hasattr(self, "_render_message"):
                self._render_message(msg, idx=len(self.chat_history) - 1)
        self._scroll_to_bottom()
