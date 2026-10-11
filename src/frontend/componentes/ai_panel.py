"""Panel unificado del tutor inteligente Glosa con soporte para dock y ruta clasica."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from nicegui import app, ui

from src.ai.context import StepRef, serialize_context
from src.ai.openrouter_ai import OpenRouterIA
from src.frontend import flags
from src.frontend.componentes.ai_panel_legacy import (
    actualizar_visibilidad_legacy,
    construir_panel_legacy,
    renderizar_chat_legacy,
    renderizar_mensaje_legacy,
)
from src.frontend.componentes.glosa_dock import GlosaDockMixin
from src.frontend.constantes import DEBOUNCE_IA_SEGUNDOS, MAX_HISTORIAL

logger = logging.getLogger(__name__)
MAX_HISTORY = MAX_HISTORIAL


def _inicializar_almacen_historial(almacen: Any) -> None:
    """Inicializa las claves requeridas en el almacen de sesion y poda historial."""
    hist = almacen.setdefault("ai_chat_history", [])
    if hist and hist[0].get("text", "").startswith("¡Hola! Estoy aquí"):
        hist = hist[1:]
    for msg in hist:
        msg.pop("api_text", None)
    almacen["ai_chat_history"] = hist[-MAX_HISTORY:] if len(hist) > MAX_HISTORY else hist
    almacen.setdefault("ai_panel_open", False)
    almacen.setdefault("ai_ctx_enabled", True)


def _recopilar_contexto_didactico(active_ui: Any, explain_focus: dict[str, Any] | None) -> str:
    """Serializa el contexto didactico del ejercicio actual agregando el foco activo."""
    if not hasattr(active_ui, "obtener_contexto_ia"):
        return ""
    try:
        ctx_obj = active_ui.obtener_contexto_ia()
        if ctx_obj is None or getattr(ctx_obj, "empty", False):
            return ""

        if explain_focus:
            columnas_foco = tuple(explain_focus["cols"]) if explain_focus.get("cols") else None
            ctx_obj.focus = StepRef(
                index=explain_focus["index"],
                total=explain_focus["total"],
                kind=explain_focus["kind"],
                op=explain_focus["op"],
                rows_before=explain_focus.get("rows_before", {}),
                rows_after=explain_focus.get("rows_after", {}),
                cols=columnas_foco,
                detail=explain_focus.get("detail"),
            )
        return serialize_context(ctx_obj)
    except Exception:
        logger.exception("Error al recopilar el contexto para la IA")
        ui.notify("No pudimos leer tu ejercicio; enviamos solo tu pregunta.", type="warning")
        return ""


class AIPanel(GlosaDockMixin):
    """Controlador unificado de interfaz para Glosa en modalidades dock y flotante."""

    @property
    def _storage(self) -> Any:
        try:
            app.storage.user.get("__test_storage__")
            return app.storage.user
        except Exception as error:
            if not hasattr(self, "_storage_warned"):
                logger.warning("Almacen de usuario no disponible: %s. Usando cliente.", error)
                self._storage_warned = True
            return app.storage.client

    @property
    def is_open(self) -> bool:
        """Devuelve True si el panel legacy esta abierto. En dock la verdad vive en html."""
        return self._storage.get("ai_panel_open", False)

    @is_open.setter
    def is_open(self, value: bool) -> None:
        self._storage["ai_panel_open"] = value

    @property
    def chat_history(self) -> list[dict[str, Any]]:
        if "ai_chat_history" not in self._storage:
            self._storage["ai_chat_history"] = []
        return self._storage["ai_chat_history"]

    @chat_history.setter
    def chat_history(self, value: list[dict[str, Any]]) -> None:
        self._storage["ai_chat_history"] = value

    def __init__(self, active_ui: Any):
        try:
            self._client = ui.context.client
        except Exception:
            self._client = None

        self.active_ui = active_ui
        self.motor_ia = OpenRouterIA()
        self.panel_container = None
        self.overlay = None
        self.chat_area = None
        self.input_field = None
        self.context_chip = None
        self.attached_context = ""
        _inicializar_almacen_historial(self._storage)
        self._last_send_time = 0.0
        self._ctx_version = 0

    def toggle(self) -> None:
        """Abre o cierra el asistente Glosa segun la modalidad activa."""
        if flags.dock_enabled():
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.alternar();")
            return
        self.is_open = not self.is_open
        actualizar_visibilidad_legacy(self)

    def open(self) -> None:
        """Abre explicitamente el asistente si se encuentra cerrado."""
        if flags.dock_enabled():
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.abrir();")
            return
        if not self.is_open:
            self.toggle()

    def programar_actualizacion_contexto(self) -> None:
        """Programa un refresco debounced de la pildora de contexto tras cambios."""
        if not flags.dock_enabled():
            return

        tarea = getattr(self, "_refresh_task", None)
        if tarea and not tarea.done():
            tarea.cancel()

        async def _debounced():
            try:
                await asyncio.sleep(DEBOUNCE_IA_SEGUNDOS)
                self.notify_context_changed()
            except asyncio.CancelledError:
                pass
            except Exception as error:
                logger.debug("Refresco de contexto cancelado o abortado: %s", error)

        coro = _debounced()
        try:
            self._refresh_task = self._spawn(coro)
        except RuntimeError:
            coro.close()

    def _collect_context(self) -> str:
        """Serializa el contexto didactico del ejercicio actual agregando el foco activo."""
        if not self._storage.get("ai_ctx_enabled", True):
            return ""
        return _recopilar_contexto_didactico(self.active_ui, getattr(self, "explain_focus", None))

    def attach_context(self) -> None:
        """Adjunta manualmente el contexto textual en la ruta legacy."""
        ctx_text = self._collect_context()
        if ctx_text:
            self.attached_context = ctx_text
            if self.context_chip:
                self.context_chip.set_visibility(True)
            ui.notify("Contexto adjuntado", type="positive")
        else:
            ui.notify("No hay datos validos para adjuntar en la vista actual.", type="warning")

    def clear_context(self) -> None:
        """Desvincula el contexto manual en la ruta legacy."""
        self.attached_context = ""
        if self.context_chip:
            self.context_chip.set_visibility(False)

    def clear_chat(self) -> None:
        """Vacia el historial de mensajes retenido."""
        self.chat_history = []
        if flags.dock_enabled():
            self.render_chat_dock()
        else:
            self.render_chat()

    def render_chat(self) -> None:
        """Renderiza la bitacora segun la modalidad activa."""
        if flags.dock_enabled():
            self.render_chat_dock()
        else:
            renderizar_chat_legacy(self)

    def _render_message(self, msg: dict[str, Any], idx: int | None = None) -> None:
        """Delega el renderizado individual de mensaje al submodulo legacy."""
        renderizar_mensaje_legacy(msg, idx=idx)

    async def send_message(self) -> None:
        """Envia el texto capturado en el area de entrada del panel legacy."""
        campo = getattr(self, "input_field", None)
        texto = campo.value if campo else ""
        await self._submit(texto)

    def renderizar_sugerencias_en_linea(self, limit: int = 2) -> None:
        """Renderiza sugerencias incrustadas en el flujo principal de la pagina."""
        from src.frontend.suggestions import chips_active, suggest
        if not chips_active() or not hasattr(self.active_ui, "obtener_senales_ia"):
            return

        senales = self._obtener_senales_interfaz()
        if not senales:
            return

        habilitado = self._storage.get("ai_ctx_enabled", True)
        suggs = suggest(senales, limit=limit, include_specific=habilitado)
        if not suggs:
            return

        from src.frontend.componentes.glosa_chips import render_chip_row
        enviando = getattr(self, "_is_sending", False)
        render_chip_row(suggs, self.ask_suggestion, variant="inline", disabled=enviando)

    def build(self) -> None:
        """Construye la interfaz de Glosa delegando a dock o a modal legacy."""
        if self._client is None:
            try:
                self._client = ui.context.client
            except Exception:
                pass

        if flags.dock_enabled():
            self.build_dock()
        else:
            construir_panel_legacy(self)
