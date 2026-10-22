"""Bitácora de conversación, mensajes y desplazamiento del panel lateral."""
from __future__ import annotations

import logging
from typing import Any
from nicegui import ui

from src.frontend.componentes.iconos import icono_svg
from src.frontend.componentes.glosa_renderizado import renderizar_texto_glosa
from src.frontend.componentes.glosa_sugerencias import renderizar_seguimientos
from src.frontend.sugerencias import sugerencias_activas
from src.frontend.catalogo_sugerencias import SEGUIMIENTOS

registro = logging.getLogger(__name__)


def construir_bitacora_lateral() -> ui.column:
    """Crea el contenedor accesible de historial de mensajes con desplazamiento vertical."""
    return ui.column().classes(
        "w-full flex-1 p-4 overflow-y-auto gap-4 glosa-area-chat"
    ).props('id="glosa-bitacora" role="log" aria-live="polite"')


def renderizar_bitacora_lateral(instancia: Any) -> None:
    """Renderiza el estado actual del historial o el mensaje de bienvenida inicial."""
    area = getattr(instancia, "area_chat", None)
    if not area:
        return
    area.clear()

    historial = getattr(instancia, "historial_chat", [])
    with area:
        if not historial:
            _renderizar_estado_vacio()
        else:
            for i, mensaje in enumerate(historial):
                _renderizar_mensaje_lateral(instancia, mensaje, es_ultimo=(i == len(historial) - 1))

    desplazar_al_final(instancia)


def _renderizar_estado_vacio() -> None:
    """Muestra la bienvenida inicial y sugerencias de capacidades de Glosa."""
    with ui.column().classes("w-full items-center justify-center h-full gap-4 text-center mt-8 texto-secundario"):
        ui.html(icono_svg("glosa")).classes("glosa-icono-vacio")
        ui.label("Hola, soy Glosa.").classes("font-bold text-lg texto-principal")
        ui.label("Explicar un paso").classes("fuente-pequena")
        ui.label("Revisar una operación").classes("fuente-pequena")
        ui.label("Aclarar un concepto").classes("fuente-pequena")


def _renderizar_contenido_burbuja(instancia: Any, enviado: bool, error: bool, texto: str, reintentar: bool) -> None:
    """Presenta un fallo con reintento opcional o un mensaje de conversación escapado."""
    if error:
        with ui.column().classes("p-3 gap-2 glosa-burbuja-error"):
            ui.label(texto).classes("whitespace-pre-wrap text-sm")
            if reintentar and hasattr(instancia, "_reintentar_ultimo_mensaje"):
                ui.button("Reintentar", icon="refresh", on_click=instancia._reintentar_ultimo_mensaje).classes(
                    "boton-principal text-xs"
                ).props("flat")
    else:
        clase_burbuja = "glosa-burbuja-usuario" if enviado else "glosa-burbuja-asistente"
        with ui.column().classes(f"p-3 {clase_burbuja}"):
            ui.html(renderizar_texto_glosa(texto)).classes("w-full")


def _renderizar_mensaje_lateral(instancia: Any, mensaje: dict[str, Any], es_ultimo: bool = False) -> None:
    """Renderiza una burbuja de mensaje con alineación y opciones contextuales."""
    enviado = mensaje.get("enviado", False)
    error = mensaje.get("error", False)
    texto = mensaje.get("texto", "")
    reintentar = mensaje.get("reintentar", False)

    alineacion_columna = "items-end" if enviado else "items-start"
    with ui.column().classes(f"w-full {alineacion_columna} mb-0"):
        _renderizar_contenido_burbuja(instancia, enviado, error, texto, reintentar)
        if es_ultimo and not enviado and not error and sugerencias_activas():
            _renderizar_seguimientos_mensaje(instancia)



def _renderizar_seguimientos_mensaje(instancia: Any) -> None:
    """Agrega las preguntas de seguimiento didáctico tras el último mensaje del asistente."""
    instancia.contenedor_seguimientos = ui.column().classes("w-full mt-2")
    with instancia.contenedor_seguimientos:
        renderizar_seguimientos(
            SEGUIMIENTOS,
            instancia.preguntar_seguimiento,
            deshabilitado=getattr(instancia, "_esta_enviando", False),
        )


def desplazar_al_final(instancia: Any) -> None:
    """Desplaza la vista del chat hacia el elemento más reciente."""
    javascript = (
        "setTimeout(() => { "
        "const elemento = document.getElementById('glosa-bitacora') || "
        "document.getElementById('ia-area-chat') || "
        "document.querySelector('.glosa-mensajes'); "
        "if(elemento) elemento.scrollTop = elemento.scrollHeight; }, 50);"
    )
    cliente = getattr(instancia, "_cliente", None)
    if cliente is not None and not getattr(cliente, "is_deleted", False):
        try:
            cliente.run_javascript(javascript)
            return
        except Exception:
            registro.warning("No se pudo desplazar la bitácora con el cliente; se intentará desde la interfaz")
    try:
        ui.run_javascript(javascript)
    except Exception:
        pass
