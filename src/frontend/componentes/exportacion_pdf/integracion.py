"""Marcado de regiones y montaje de la acción compartida de exportación."""
from nicegui import ui

from src.frontend.controladores.exportacion_pdf.vigencia import EnlacePDF
from .boton import renderizar_boton_pdf


def region_pdf(clave: str):
    """Crea una columna capturable de ancho completo para el contenido del resultado."""
    return ui.column().classes('w-full min-w-0').props(f'data-pdf-captura={clave}')


def completar_exportacion(vista, herramienta: str, resultado: dict, enlace: EnlacePDF) -> None:
    """Marca el reproductor visible y conecta la actualización del único botón PDF."""
    reproductor = getattr(vista, 'reproductor_pasos', None)
    if reproductor is not None and reproductor.tarjeta is not None:
        reproductor.tarjeta.props(f'data-pdf-captura={herramienta}-procedimiento')
    control = renderizar_boton_pdf(herramienta, resultado, enlace)
    vista.actualizar_exportacion_pdf = control.actualizar
