"""Controles compartidos de captura de una ecuación por fila."""
from collections.abc import Callable
from functools import partial

from nicegui import ui

from src.backend.constantes import MAXIMO_CARACTERES_ECUACIONES
from src.frontend.componentes.aplicacion.base.simbolos import renderizar_boton_simbolos


def crear_cabecera_ecuaciones(al_redimensionar: Callable, montar_accion: Callable | None = None) -> tuple:
    """Monta el título, la acción opcional y los botones de quitar y añadir."""
    with ui.row().classes('w-full justify-between items-center mb-6 gap-2 flex-wrap'):
        ui.label('Sistema de Ecuaciones').classes('text-lg font-bold texto-principal')
        if montar_accion is not None:
            montar_accion()
        with ui.row().classes('gap-2 ml-auto items-center'):
            renderizar_boton_simbolos()
            quitar = _boton_dimension('remove', 'Quitar ecuación', partial(al_redimensionar, -1))
            agregar = _boton_dimension('add', 'Añadir ecuación', partial(al_redimensionar, 1))
    return quitar, agregar


def _boton_dimension(icono: str, etiqueta: str, accion: Callable) -> ui.button:
    return ui.button(icon=icono, on_click=accion, color=None).classes(
        'boton-icono p-0',
    ).props(f'ripple=false aria-label="{etiqueta}"').tooltip(etiqueta)


def montar_filas_ecuaciones(contenedor: ui.column, valores: list[str], al_editar: Callable) -> list[ui.input]:
    """Reemplaza las filas con los valores indicados y devuelve sus campos en orden."""
    contenedor.clear()
    with contenedor:
        return [_crear_entrada(indice, valor, al_editar) for indice, valor in enumerate(valores)]


def _crear_entrada(indice: int, valor: str, al_editar: Callable) -> ui.input:
    numero = indice + 1
    with ui.row().classes('w-full items-center gap-3 no-wrap mb-3'):
        ui.label(f'{numero}.').classes('font-bold texto-secundario w-6 text-right shrink-0').props('aria-hidden=true')
        return ui.input(
            value=valor, placeholder=f'Ej. 2x + 3y = {indice * 2 + 4}', on_change=al_editar,
        ).classes('matriz-entrada flex-1 min-w-0').props(
            f'borderless autocomplete="new-password" name="eq{indice}" data-ecuaciones-indice="{indice}" '
            f'aria-label="Ecuación {numero}" maxlength={MAXIMO_CARACTERES_ECUACIONES}'
        )
