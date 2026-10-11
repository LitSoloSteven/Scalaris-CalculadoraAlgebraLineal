"""Renderizado perezoso del indice de fases del reproductor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from src.frontend.componentes.reproductor_pasos.catalogo import html_chip_tipo

if TYPE_CHECKING:
    from src.frontend.componentes.reproductor_pasos.reproductor import ReproductorPasos


def construir_indice(reproductor: ReproductorPasos) -> None:
    """Dibuja el indice por fases cuando hay mas de un grupo."""
    if len(reproductor.grupos) <= 1:
        return
    with ui.expansion('Indice de pasos por fases', icon='list').classes(
        'w-full panel-card mt-4 timeline-expansion'
    ).props('header-class="font-bold text-main"'):
        with ui.column().classes('w-full p-2 gap-2'):
            for indice, grupo in enumerate(reproductor.grupos):
                _crear_grupo(reproductor, indice, grupo)


def _crear_grupo(reproductor: ReproductorPasos, indice: int, grupo) -> None:
    """Crea una fase expandible con su cargador perezoso."""
    with ui.expansion(grupo.titulo, caption=grupo.resumen).classes(
        'w-full border border-[var(--border-input)] rounded-lg'
    ).props('header-class="font-semibold text-main text-sm"') as expansion:
        contenedor = ui.column().classes('w-full p-2 gap-1')
        expansion.on_value_change(_crear_cargador(reproductor, indice, grupo, contenedor))


def _crear_cargador(reproductor: ReproductorPasos, indice: int, grupo, contenedor):
    """Crea un callback que llena la fase solo la primera vez que se abre."""
    def cargar(evento):
        if not evento.value or indice in reproductor.grupos_cargados:
            return
        reproductor.grupos_cargados.add(indice)
        _cargar_pasos(reproductor, grupo, contenedor)

    return cargar


def _cargar_pasos(reproductor: ReproductorPasos, grupo, contenedor) -> None:
    """Renderiza los botones de paso de una fase abierta."""
    with contenedor:
        for indice_paso in grupo.indices_pasos:
            if 0 <= indice_paso < len(reproductor.pasos):
                _renderizar_boton_paso(reproductor, indice_paso)


def _renderizar_boton_paso(reproductor: ReproductorPasos, indice_paso: int) -> None:
    """Dibuja un boton de acceso directo a un paso dentro del indice."""
    paso = reproductor.pasos[indice_paso]
    with ui.button(
        color=None,
        on_click=lambda evento, destino=indice_paso: reproductor._seleccionar_desde_indice(destino),
    ).classes('btn-ghost w-full justify-start py-2 px-3 text-left').props('ripple=false'):
        with ui.row().classes('items-center gap-3 w-full'):
            ui.html(html_chip_tipo(paso.tipo, paso.etiqueta_tipo))
            ui.label(f"{indice_paso + 1}. {paso.descripcion}").classes(
                'text-sm font-medium text-main'
            )

