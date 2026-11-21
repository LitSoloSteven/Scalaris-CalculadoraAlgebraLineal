"""Componente de selección de tema reutilizable para Scalaris."""
from __future__ import annotations

from nicegui import ui
from src.frontend.componentes.aplicacion.base.iconos import icono_svg
from src.frontend.componentes.aplicacion.base.menu_accesible import vincular_estado_menu


_TEMAS = (("Papel", "papel"), ("Marea", "marea"), ("Medianoche", "medianoche"))


def renderizar_boton_tema(mostrar_nombre: bool = False):
    """Renderiza el selector de tema y muestra su nombre si se solicita."""
    clases = "selector-tema-textual" if mostrar_nombre else "boton-icono p-0 texto-principal"
    boton_tema = ui.button(color=None).classes(clases).props(
        'flat ripple=false data-sonido="apertura" aria-haspopup="menu" aria-expanded="false"'
    )
    if not mostrar_nombre:
        boton_tema.props('aria-label="Seleccionar Tema"')

    with boton_tema:
        ui.html(icono_svg("temas"))
        if mostrar_nombre:
            ui.label("Tema").classes("sr-only")
            for etiqueta, identificador in _TEMAS:
                ui.label(etiqueta).props(f'data-inicio-nombre-tema="{identificador}"')
        menu_tema = ui.menu().classes("p-2 min-w-[150px]")
        vincular_estado_menu(boton_tema, menu_tema)

        with menu_tema:
            _renderizar_opciones_tema()

    return boton_tema


def _renderizar_opciones_tema() -> None:
    """Genera las tres alternativas de tema gráfico con su muestra de color."""
    for etiqueta, id_tema in _TEMAS:
        with ui.menu_item().classes("rounded-lg mb-1 flex items-center gap-3 w-full").props(
            f'role="menuitemradio" aria-checked="false" data-tema-opcion="{id_tema}"'
        ):
            ui.html(f'<div class="tema-muestra tema-muestra-{id_tema}"></div>')
            ui.label(etiqueta).classes("flex-1")
            ui.html(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
                f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
                f'class="tema-marca-activa" aria-hidden="true">'
                f'<polyline points="20 6 9 17 4 12"></polyline></svg>'
            )
