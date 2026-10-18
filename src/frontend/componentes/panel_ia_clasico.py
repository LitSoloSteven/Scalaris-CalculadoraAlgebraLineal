"""Panel modal flotante clásico de Glosa cuando el panel lateral está inactivo."""
from __future__ import annotations

import html
import json
from typing import Any
from nicegui import ui
from src.frontend.componentes.glosa_entrada import EstiloEntradaGlosa, construir_entrada_glosa


def construir_panel_clasico(instancia: Any) -> None:
    """Construye la superposición fija y la tarjeta flotante del panel clásico."""
    instancia.superposicion = ui.element("div").classes("ia-panel-superposicion")
    instancia.superposicion.on("click", instancia.alternar)

    instancia.contenedor_panel = ui.column().classes("no-wrap ia-panel-superficie ia-panel-tarjeta")
    with instancia.contenedor_panel:
        _construir_cabecera_clasico(instancia)
        instancia.area_chat = ui.column().classes("w-full flex-1 p-4 overflow-y-auto gap-2").props(
            'id="ia-area-chat"'
        )
        instancia.renderizar_chat()
        _construir_pie_clasico(instancia)

    actualizar_visibilidad_clasico(instancia)


def _construir_cabecera_clasico(instancia: Any) -> None:
    """Construye la barra superior con acciones de contexto, borrado y cierre."""
    with ui.row().classes("w-full items-center justify-between p-4 border-b border-[var(--border-input)]"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("smart_toy", size="sm").classes("texto-acento")
            ui.label("Glosa").classes("font-bold text-lg texto-principal")

        with ui.row().classes("gap-2"):
            ui.button(icon="attach_file", on_click=instancia.adjuntar_contexto, color=None).classes(
                "boton-icono w-8 h-8 p-0 texto-secundario"
            ).props('ripple=false aria-label="Adjuntar sistema actual"').tooltip("Adjuntar sistema actual")
            ui.button(icon="delete_sweep", on_click=instancia.limpiar_chat, color=None).classes(
                "boton-icono w-8 h-8 p-0 texto-secundario"
            ).props('ripple=false aria-label="Limpiar conversación"').tooltip("Limpiar conversación")
            ui.button(icon="close", on_click=instancia.alternar, color=None).classes(
                "boton-icono w-8 h-8 p-0"
            ).props('ripple=false aria-label="Cerrar Glosa"').tooltip("Cerrar")


def _construir_pie_clasico(instancia: Any) -> None:
    """Construye el chip de contexto adjunto y el área de entrada del panel clasico."""
    with ui.column().classes("w-full p-4 border-t border-[var(--border-input)] bg-[var(--bg-elevated)]"):
        instancia.capsula_contexto = ui.chip(
            "Sistema adjunto", icon="data_object", color=None
        ).props("removable").on("remove", instancia.limpiar_contexto).classes("mb-2 distintivo-exito")
        instancia.capsula_contexto.set_visibility(bool(instancia.contexto_adjuntado))

        construir_entrada_glosa(instancia, EstiloEntradaGlosa(
            clases_contenedor="w-full items-end gap-2 ia-contenedor-entrada",
            clases_campo="flex-1 matriz-entrada text-sm glosa-campo-entrada",
            clases_boton="boton-principal w-10 h-10 p-0 mb-1 glosa-boton-enviar",
            texto_ayuda="Pregunta algo...",
            etiqueta_envio="Enviar mensaje",
        ))


def actualizar_visibilidad_clasico(instancia: Any) -> None:
    """Aplica las clases y visibilidad modal según el estado abierto/cerrado."""
    if not instancia.contenedor_panel or not instancia.superposicion:
        return
    if instancia.esta_abierto:
        instancia.contenedor_panel.classes(remove="translate-x-[calc(100%+32px)] opacity-0 invisible pointer-events-none")
        instancia.contenedor_panel.classes(add="translate-x-0 opacity-100 visible pointer-events-auto")
        instancia.superposicion.classes(remove="opacity-0 pointer-events-none").classes(add="opacity-100 pointer-events-auto")
    else:
        instancia.contenedor_panel.classes(remove="translate-x-0 opacity-100 visible pointer-events-auto")
        instancia.contenedor_panel.classes(add="translate-x-[calc(100%+32px)] opacity-0 invisible pointer-events-none")
        instancia.superposicion.classes(remove="opacity-100 pointer-events-auto").classes(add="opacity-0 pointer-events-none")


def renderizar_chat_clasico(instancia: Any) -> None:
    """Renderiza la lista de mensajes en el contenedor de chat del panel clasico."""
    if not instancia.area_chat:
        return
    instancia.area_chat.clear()

    with instancia.area_chat:
        for i, mensaje in enumerate(instancia.historial_chat):
            renderizar_mensaje_clasico(mensaje, indice=i)

    ui.run_javascript(
        "setTimeout(() => { const elemento = document.getElementById('ia-area-chat'); "
        "if(elemento) elemento.scrollTop = elemento.scrollHeight; }, 100);"
    )


def renderizar_mensaje_clasico(mensaje: dict[str, Any], indice: int | None = None) -> None:
    """Renderiza un mensaje individual con burbuja adaptada al remitente."""
    texto = mensaje.get("texto", "")
    enviado = mensaje.get("enviado", False)
    alineacion = "justify-end" if enviado else "justify-start"
    clase_burbuja = "glosa-burbuja-usuario" if enviado else "glosa-burbuja-asistente"

    with ui.row().classes(f"w-full {alineacion} mb-4"):
        contenedor = ui.column().classes(f"p-3 {clase_burbuja}")
        with contenedor:
            identificador_mensaje = f"ia-mensaje-{id(texto)}-{indice}" if not enviado and mensaje.get("animar") else None
            if identificador_mensaje:
                mensaje["animar"] = False
                ui.html(f'<div id="{identificador_mensaje}"></div>').classes("whitespace-pre-wrap matematicas-etiqueta")
                ui.timer(0.05, lambda texto_mensaje=texto, identificador_mensaje=identificador_mensaje: ui.run_javascript(
                    f'window.scalaris.efectoMaquinaEscribir("{identificador_mensaje}", {json.dumps(texto_mensaje)}, 15)'
                ), once=True)
            else:
                ui.html(html.escape(texto).replace("\n", "<br>")).classes("whitespace-pre-wrap matematicas-etiqueta")
