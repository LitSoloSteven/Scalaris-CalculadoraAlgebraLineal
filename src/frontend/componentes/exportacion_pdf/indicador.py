"""Indicadores de progreso compuestos sin el spinner SVG del botón Quasar."""
from nicegui import ui

from src.frontend import textos


def crear_indicador():
    """Crea un estado accesible oculto; devuelve el elemento para activar su progreso."""
    indicador = ui.element('span').classes('pdf-indicador').props(
        f'role=status aria-label="{textos.PDF_CARGANDO}"')
    indicador.set_visibility(False)
    return indicador


def cargar_indicador(indicador, ocupado: bool) -> None:
    """Activa la animación y su capa solo durante la operación si el elemento aún existe."""
    if indicador.is_deleted:
        return
    if ocupado:
        indicador.props('data-destacada-activa')
    else:
        indicador.props(remove='data-destacada-activa')
    indicador.set_visibility(ocupado)
