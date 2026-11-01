"""Montaje temporal de la entrada y pasos sin navegar el reproductor visible."""
from contextlib import contextmanager

from nicegui import ui
from src.frontend import textos
from src.frontend.componentes.reproductor_pasos.textos import formatear_descripcion_html
from src.frontend.controladores.exportacion_pdf.secuencia import seleccionar_intermedios
from .entrada import renderizar_entrada


@contextmanager
def preparar_secuencia(herramienta: str, enlace):
    """Monta regiones temporales del cálculo vigente y las elimina incluso al cancelar."""
    contenedor = enlace.estado()[0]
    with contenedor:
        temporal = ui.column().classes('pdf-secuencia').props('aria-hidden=true inert data-pdf-secuencia')
    try:
        with temporal:
            with _region(f'{herramienta}-entrada'):
                renderizar_entrada(enlace.entrada(), herramienta)
            reproductor = (getattr(enlace.vista, 'reproductor_pasos', None)
                           or getattr(enlace.vista, 'reproductor', None))
            if reproductor is not None:
                _renderizar_pasos(herramienta, reproductor)
        yield temporal
    finally:
        if not temporal.is_deleted:
            temporal.delete()


def _region(clave: str):
    return ui.column().classes('w-full gap-4').props(f'data-pdf-captura={clave}')


def _renderizar_pasos(herramienta: str, reproductor) -> None:
    for numero, paso in enumerate(seleccionar_intermedios(reproductor.pasos), 1):
        with _region(f'{herramienta}-paso-{numero}'):
            ui.label(textos.PDF_PASO_ORIGINAL.format(numero=paso.indice + 1,
                                                   total=len(reproductor.pasos))).classes('text-h6')
            ui.html(formatear_descripcion_html(paso.descripcion))
            if paso.explicacion and paso.explicacion != paso.descripcion:
                ui.html(formatear_descripcion_html(paso.explicacion))
            cuerpo = ui.column().classes('w-full')
            reproductor.renderizar_cuerpo(paso, cuerpo)
