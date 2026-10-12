"""Componente de selección de tema reutilizable para Scalaris."""
from __future__ import annotations

from nicegui import ui
from src.frontend.componentes.icons import icon_svg


def renderizar_boton_tema():
    """Renderiza el botón de tema con su menú desplegable accesible."""
    boton_tema = ui.button(color=None).classes("btn-neo-icon p-0 text-main").props(
        'flat ripple=false aria-label="Seleccionar Tema" aria-haspopup="menu" aria-expanded="false"'
    ).tooltip("Seleccionar Tema")

    with boton_tema:
        ui.html(icon_svg("temas"))
        menu_tema = ui.menu().classes("p-2 min-w-[150px]")
        menu_tema.on("show", lambda _, boton=boton_tema: boton.props('aria-expanded="true"'))
        menu_tema.on("hide", lambda _, boton=boton_tema: boton.props('aria-expanded="false"'))

        with menu_tema:
            _renderizar_opciones_tema()

    return boton_tema


def _renderizar_opciones_tema() -> None:
    """Genera las tres alternativas de tema gráfico con su muestra de color."""
    opciones = (
        ("Papel", "papel"),
        ("Marea", "marea"),
        ("Medianoche", "medianoche"),
    )
    for etiqueta, id_tema in opciones:
        with ui.menu_item(
            on_click=lambda tema=id_tema: ui.run_javascript(f"window.scalaris.tema.establecer('{tema}')")
        ).classes("rounded-lg mb-1 flex items-center gap-3 w-full"):
            ui.html(f'<div class="tema-muestra tema-muestra-{id_tema}"></div>')
            ui.label(etiqueta).classes("flex-1")
            ui.html(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                f'class="tema-marca-activa tema-marca-{id_tema}">'
                f'<polyline points="20 6 9 17 4 12"></polyline></svg>'
            )
