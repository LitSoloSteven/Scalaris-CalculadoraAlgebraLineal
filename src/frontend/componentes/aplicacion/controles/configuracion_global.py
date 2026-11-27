"""Diálogo accesible de configuración global para tema y efectos de sonido."""
from __future__ import annotations

import json
from nicegui import ui

from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.componentes.aplicacion.controles.selector_tema import TEMAS_DISPONIBLES


_MARCA_ACTIVA_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
    'class="tema-marca-activa" aria-hidden="true">'
    '<polyline points="20 6 9 17 4 12"></polyline></svg>'
)


def _renderizar_bloque_temas() -> None:
    """Renderiza el grupo de opciones de tema reutilizando la selección cliente."""
    with ui.element("div").classes("configuracion-bloque"):
        ui.label("Tema").classes("configuracion-subtitulo")
        with ui.element("div").classes("configuracion-temas").props(
            'role="radiogroup" aria-label="Tema de la interfaz"'
        ):
            for etiqueta, id_tema in TEMAS_DISPONIBLES:
                _renderizar_opcion_tema(etiqueta, id_tema)


def _renderizar_opcion_tema(etiqueta: str, id_tema: str) -> None:
    with ui.button(color=None).classes("configuracion-opcion-tema").props(
        f'flat no-caps ripple=false role="menuitemradio" aria-checked="false" '
        f'data-tema-opcion="{id_tema}"'
    ):
        ui.html(
            f'<div class="tema-muestra tema-muestra-{id_tema}" aria-hidden="true"></div>',
            tag="span",
        ).classes("shrink-0 flex items-center")
        ui.label(etiqueta).classes("flex-1 text-left")
        ui.html(_MARCA_ACTIVA_SVG)


def _renderizar_bloque_sonido() -> None:
    """Renderiza el conmutador nativo de efectos de sonido sincronizado con el cliente."""
    with ui.element("div").classes("configuracion-bloque"):
        ui.label("Sonido").classes("configuracion-subtitulo")
        with ui.element("button").classes("configuracion-sonido-boton").props(
            'type="button" data-sonido-control aria-label="Silenciar sonidos" '
            'aria-pressed="false" title="Silenciar sonidos"'
        ):
            with ui.element("span").classes("configuracion-sonido-inicio"):
                ui.html(icono_svg("sonido")).props('data-sonido-icono="activo" aria-hidden="true"')
                ui.html(icono_svg("sonido_silenciado")).props(
                    'data-sonido-icono="silenciado" aria-hidden="true" hidden'
                )
                ui.label("Efectos de sonido")
            ui.label("Activados").classes("configuracion-sonido-estado").props("data-sonido-estado")


def renderizar_boton_configuracion() -> ui.button:
    """Crea el botón de cabecera y el diálogo modal compartido de Configuración."""
    ui.add_head_html('<link rel="stylesheet" href="/assets/css/utilidades/configuracion_global.css">')
    boton = ui.button(color=None).classes(
        "boton-icono p-0 texto-principal navegacion-configuracion"
    ).props(
        'flat ripple=false data-sonido="apertura" data-configuracion-abrir '
        'data-selector-tema-boton aria-label="Configuración" aria-haspopup="dialog"'
    ).tooltip("Configuración")
    with boton:
        ui.html(icono_svg("configuracion"))

    with ui.dialog().props(
        'aria-labelledby="configuracion-titulo" aria-modal="true" '
        'transition-show=scale transition-hide=scale'
    ) as dialogo:
        with ui.card().classes("panel-tarjeta configuracion-dialogo"):
            with ui.element("div").classes("configuracion-cabecera"):
                ui.html('<h2 id="configuracion-titulo" class="configuracion-titulo">Configuración</h2>')
                ui.button(icon="close", on_click=dialogo.close, color=None).classes(
                    "boton-icono p-0"
                ).props('flat ripple=false data-sonido="cierre" aria-label="Cerrar configuración"').tooltip("Cerrar")
            _renderizar_bloque_temas()
            _renderizar_bloque_sonido()

    def devolver_foco() -> None:
        """Restituye el foco al activador en cabecera cuando el diálogo se cierra."""
        if not boton.is_deleted and boton.visible:
            ui.run_javascript(f"document.getElementById({json.dumps(boton.html_id)})?.focus();")

    boton.on_click(dialogo.open)
    dialogo.on("hide", devolver_foco)
    return boton
