"""Bitácora de conversación, renderizado de mensajes y desplazamiento del dock."""
from __future__ import annotations

import logging
from typing import Any
from nicegui import ui

from src.frontend.componentes.icons import icon_svg
from src.frontend.componentes.glosa_render import render_glosa_text
from src.frontend.componentes.glosa_chips import render_followups
from src.frontend.suggestions import FOLLOW_UPS, chips_active

logger = logging.getLogger(__name__)


def construir_bitacora_dock() -> ui.column:
    """Crea el contenedor accesible de historial de mensajes con desplazamiento vertical."""
    return ui.column().classes(
        "w-full flex-1 p-4 overflow-y-auto gap-4 glosa-area-chat"
    ).props('id="glosa-log" role="log" aria-live="polite"')


def renderizar_bitacora_dock(instancia: Any) -> None:
    """Renderiza el estado actual del historial o el mensaje de bienvenida inicial."""
    area = getattr(instancia, "chat_area", None)
    if not area:
        return
    area.clear()

    historial = getattr(instancia, "chat_history", [])
    with area:
        if not historial:
            _renderizar_estado_vacio()
        else:
            for i, msg in enumerate(historial):
                _renderizar_mensaje_dock(instancia, msg, is_last=(i == len(historial) - 1))

    desplazar_al_final(instancia)


def _renderizar_estado_vacio() -> None:
    """Muestra la bienvenida inicial y sugerencias de capacidades de Glosa."""
    with ui.column().classes("w-full items-center justify-center h-full gap-4 text-center mt-8 text-sec"):
        ui.html(icon_svg("glosa")).classes("glosa-icono-vacio")
        ui.label("Hola, soy Glosa.").classes("font-bold text-lg text-main")
        ui.label("Explicar un paso").classes("fs-small")
        ui.label("Revisar una operación").classes("fs-small")
        ui.label("Aclarar un concepto").classes("fs-small")


def _renderizar_contenido_burbuja(instancia: Any, sent: bool, error: bool, text: str, retry: bool) -> None:
    """Renderiza el contenido de la burbuja, diferenciando error vs mensaje regular."""
    if error:
        with ui.column().classes("p-3 gap-2 glosa-burbuja-error"):
            ui.label(text).classes("whitespace-pre-wrap text-sm")
            if retry and hasattr(instancia, "_retry_last_dock"):
                ui.button("Reintentar", icon="refresh", on_click=instancia._retry_last_dock).classes(
                    "btn-primary text-xs"
                ).props("flat")
    else:
        clase_burbuja = "glosa-burbuja-usuario" if sent else "glosa-burbuja-asistente"
        with ui.column().classes(f"p-3 {clase_burbuja}"):
            ui.html(render_glosa_text(text)).classes("w-full")


def _renderizar_mensaje_dock(instancia: Any, msg: dict[str, Any], is_last: bool = False) -> None:
    """Renderiza una burbuja de mensaje con alineación y opciones contextuales."""
    sent = msg.get("sent", False)
    error = msg.get("error", False)
    text = msg.get("text", "")
    retry = msg.get("retry", False)

    col_align = "items-end" if sent else "items-start"
    with ui.column().classes(f"w-full {col_align} mb-0"):
        _renderizar_contenido_burbuja(instancia, sent, error, text, retry)
        if is_last and not sent and not error and chips_active():
            _renderizar_seguimientos_mensaje(instancia)



def _renderizar_seguimientos_mensaje(instancia: Any) -> None:
    """Agrega las preguntas de seguimiento didáctico tras el último mensaje del asistente."""
    instancia.followups_container = ui.column().classes("w-full mt-2")
    with instancia.followups_container:
        render_followups(
            FOLLOW_UPS,
            instancia.ask_followup,
            disabled=getattr(instancia, "_is_sending", False),
        )


def desplazar_al_final(instancia: Any) -> None:
    """Desplaza la vista del chat hacia el elemento más reciente."""
    js = (
        "setTimeout(() => { "
        "const el = document.getElementById('glosa-log') || "
        "document.getElementById('ai-chat-area') || "
        "document.querySelector('.glosa-messages'); "
        "if(el) el.scrollTop = el.scrollHeight; }, 50);"
    )
    cliente = getattr(instancia, "_client", None)
    if cliente is not None and not getattr(cliente, "is_deleted", False):
        try:
            cliente.run_javascript(js)
            return
        except Exception as error:
            logger.debug("Fallo al desplazar con cliente: %s", error)
    try:
        ui.run_javascript(js)
    except Exception:
        pass
