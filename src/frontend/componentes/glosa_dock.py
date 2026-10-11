"""Componente principal GlosaDockMixin para el asistente flotante y lateral."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from nicegui import ui

from src.frontend.componentes.glosa_bitacora import (
    construir_bitacora_dock,
    desplazar_al_final,
    renderizar_bitacora_dock,
)
from src.frontend.componentes.glosa_cabecera import construir_cabecera_dock
from src.frontend.componentes.glosa_chips import render_chip_row
from src.frontend.componentes.glosa_envio import EnvioGlosaMixin
from src.frontend.componentes.glosa_foco import FocoGlosaMixin
from src.frontend.componentes.glosa_pie import (
    construir_fab_y_scrim,
    construir_pie_dock,
    renderizar_pildora_contexto,
)
from src.frontend.componentes.tareas import lanzar_tarea
from src.frontend.constantes import MAX_HISTORIAL
from src.frontend.suggestions import chips_active, suggest

logger = logging.getLogger(__name__)
MAX_HISTORY = MAX_HISTORIAL


class GlosaDockMixin(FocoGlosaMixin, EnvioGlosaMixin):
    """Orquestador del dock de Glosa que ensambla cabecera, bitácora y pie."""

    def _spawn(self, coro: Any) -> asyncio.Task:
        """Crea una tarea async que entra al contexto del cliente antes de ejecutar la corrutina."""
        return lanzar_tarea(getattr(self, "_client", None), coro)

    def _enviar_mensaje_asincrono(self, texto: str) -> asyncio.Task:
        """Lanza el envío asegurando el contexto del cliente."""
        return self._spawn(self._submit(texto))

    def open(self) -> None:
        """Abre el dock visual invocando la función correspondiente en cliente JS."""
        ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.abrir();")

    def build_dock(self) -> None:
        """Construye la estructura completa del dock lateral accesible."""
        with ui.element("aside").classes("glosa-dock flex flex-col no-wrap").props(
            'id="glosa-dock" role="complementary" aria-label="Glosa, asistente de álgebra lineal" data-glosa-keep'
        ):
            construir_cabecera_dock(self.clear_chat)
            self.chat_area = construir_bitacora_dock()
            self.render_chat_dock()
            construir_pie_dock(self)

        construir_fab_y_scrim()

    def _toggle_ctx(self, e: Any) -> None:
        """Alterna la inclusión automática de contexto algebraico."""
        self._storage["ai_ctx_enabled"] = e.value
        self.render_context_pill.refresh()

    @ui.refreshable
    def render_context_pill(self) -> None:
        """Refresca la vista de la píldora de contexto en el pie del dock."""
        renderizar_pildora_contexto(self)

    def notify_context_changed(self) -> None:
        """Notifica al dock que el contexto del ejercicio cambió."""
        if hasattr(self, "_ctx_version"):
            self._ctx_version += 1
        self.render_context_pill.refresh()
        self._render_dock_chips()

    def _render_dock_chips(self) -> None:
        """Actualiza la lista de preguntas sugeridas en base a señales de la interfaz."""
        if not hasattr(self, "dock_chips_container") or not self.dock_chips_container:
            return
        if not chips_active():
            self.dock_chips_container.clear()
            return

        senales = self._obtener_senales_interfaz()
        habilitado = self._storage.get("ai_ctx_enabled", True)
        suggs = suggest(senales, limit=3, include_specific=habilitado)
        ids = tuple(s.id for s in suggs)

        if ids == getattr(self, "_last_chips_ids", ()) and not getattr(self, "_force_chips_render", False):
            return

        self._last_chips_ids = ids
        self._force_chips_render = False
        self.dock_chips_container.clear()
        if not suggs:
            return

        with self.dock_chips_container:
            enviando = getattr(self, "_is_sending", False)
            render_chip_row(suggs, self.ask_suggestion, variant="dock", disabled=enviando)

    def _obtener_senales_interfaz(self) -> Any:
        """Recupera con tolerancia a fallos las señales didácticas del ejercicio activo."""
        if hasattr(self.active_ui, "obtener_senales_ia"):
            try:
                return self.active_ui.obtener_senales_ia()
            except Exception as error:
                logger.error("Error en obtener_senales_ia: %s", error)
        return None

    def render_chat_dock(self) -> None:
        """Invoca el renderizado reactivo del área de bitácora."""
        renderizar_bitacora_dock(self)

    def _scroll_to_bottom(self) -> None:
        """Desplaza el scroll de la bitácora al extremo inferior."""
        desplazar_al_final(self)
