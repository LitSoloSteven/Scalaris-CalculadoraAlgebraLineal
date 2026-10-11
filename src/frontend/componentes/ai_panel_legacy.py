"""Panel modal flotante legacy para visualización de Glosa cuando el dock está inactivo."""
from __future__ import annotations

import html
import json
from typing import Any
from nicegui import ui


def construir_panel_legacy(instancia: Any) -> None:
    """Construye la superposición fija y la tarjeta flotante del panel clásico."""
    instancia.overlay = ui.element("div").classes("ai-panel-superposicion")
    instancia.overlay.on("click", instancia.toggle)

    instancia.panel_container = ui.column().classes("no-wrap ai-panel-card ai-panel-tarjeta")
    with instancia.panel_container:
        _construir_cabecera_legacy(instancia)
        instancia.chat_area = ui.column().classes("w-full flex-1 p-4 overflow-y-auto gap-2").props(
            'id="ai-chat-area"'
        )
        instancia.render_chat()
        _construir_pie_legacy(instancia)

    actualizar_visibilidad_legacy(instancia)


def _construir_cabecera_legacy(instancia: Any) -> None:
    """Construye la barra superior con acciones de contexto, borrado y cierre."""
    with ui.row().classes("w-full items-center justify-between p-4 border-b border-[var(--border-input)]"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("smart_toy", size="sm").classes("text-accent")
            ui.label("Glosa").classes("font-bold text-lg text-main")

        with ui.row().classes("gap-2"):
            ui.button(icon="attach_file", on_click=instancia.attach_context, color=None).classes(
                "btn-neo-icon w-8 h-8 p-0 text-sec"
            ).props('ripple=false aria-label="Adjuntar sistema actual"').tooltip("Adjuntar sistema actual")
            ui.button(icon="delete_sweep", on_click=instancia.clear_chat, color=None).classes(
                "btn-neo-icon w-8 h-8 p-0 text-sec"
            ).props('ripple=false aria-label="Limpiar conversación"').tooltip("Limpiar conversación")
            ui.button(icon="close", on_click=instancia.toggle, color=None).classes(
                "btn-neo-icon w-8 h-8 p-0"
            ).props('ripple=false aria-label="Cerrar Glosa"').tooltip("Cerrar")


def _construir_pie_legacy(instancia: Any) -> None:
    """Construye el chip de contexto adjunto y el área de entrada del panel legacy."""
    with ui.column().classes("w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)]"):
        instancia.context_chip = ui.chip(
            "Sistema adjunto", icon="data_object", color=None
        ).props("removable").on("remove", instancia.clear_context).classes("mb-2 badge-success")
        instancia.context_chip.set_visibility(bool(instancia.attached_context))

        with ui.row().classes("w-full items-end gap-2 ai-input-wrapper"):
            instancia.input_field = ui.textarea(placeholder="Pregunta algo...").classes(
                "flex-1 matrix-input text-sm glosa-campo-entrada"
            ).props("borderless autogrow")
            instancia.input_field.on("keydown.enter.prevent.exact", instancia.send_message)

            ui.button(icon="send", on_click=instancia.send_message, color=None).classes(
                "btn-primary w-10 h-10 p-0 mb-1 glosa-boton-enviar"
            ).props('ripple=false aria-label="Enviar mensaje"').tooltip("Enviar")


def actualizar_visibilidad_legacy(instancia: Any) -> None:
    """Aplica las clases y visibilidad modal según el estado abierto/cerrado."""
    if not instancia.panel_container or not instancia.overlay:
        return
    if instancia.is_open:
        instancia.panel_container.classes(remove="translate-x-[calc(100%+32px)] opacity-0 invisible pointer-events-none")
        instancia.panel_container.classes(add="translate-x-0 opacity-100 visible pointer-events-auto")
        instancia.overlay.classes(remove="opacity-0 pointer-events-none").classes(add="opacity-100 pointer-events-auto")
    else:
        instancia.panel_container.classes(remove="translate-x-0 opacity-100 visible pointer-events-auto")
        instancia.panel_container.classes(add="translate-x-[calc(100%+32px)] opacity-0 invisible pointer-events-none")
        instancia.overlay.classes(remove="opacity-100 pointer-events-auto").classes(add="opacity-0 pointer-events-none")


def renderizar_chat_legacy(instancia: Any) -> None:
    """Renderiza la lista de mensajes en el contenedor de chat del panel legacy."""
    if not instancia.chat_area:
        return
    instancia.chat_area.clear()

    with instancia.chat_area:
        for i, msg in enumerate(instancia.chat_history):
            renderizar_mensaje_legacy(msg, idx=i)

    ui.run_javascript(
        "setTimeout(() => { const el = document.getElementById('ai-chat-area'); "
        "if(el) el.scrollTop = el.scrollHeight; }, 100);"
    )


def renderizar_mensaje_legacy(msg: dict[str, Any], idx: int | None = None) -> None:
    """Renderiza un mensaje individual con burbuja adaptada al remitente."""
    text = msg.get("text", "")
    sent = msg.get("sent", False)
    align = "justify-end" if sent else "justify-start"
    clase_burbuja = "glosa-burbuja-usuario" if sent else "glosa-burbuja-asistente"

    with ui.row().classes(f"w-full {align} mb-4"):
        container = ui.column().classes(f"p-3 {clase_burbuja}")
        with container:
            msg_id = f"ai-msg-{id(text)}-{idx}" if not sent and msg.get("animate") else None
            if msg_id:
                msg["animate"] = False
                ui.html(f'<div id="{msg_id}"></div>').classes("whitespace-pre-wrap math-label")
                ui.timer(0.05, lambda t=text, mid=msg_id: ui.run_javascript(
                    f'typewriterEffect("{mid}", {json.dumps(t)}, 15)'
                ), once=True)
            else:
                ui.html(html.escape(text).replace("\n", "<br>")).classes("whitespace-pre-wrap math-label")
