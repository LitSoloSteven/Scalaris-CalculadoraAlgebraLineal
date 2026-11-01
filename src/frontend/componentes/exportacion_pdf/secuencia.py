"""Montaje temporal de la entrada y pasos sin navegar el reproductor visible."""
from contextlib import contextmanager

from nicegui import ui
from src.frontend import textos
from src.frontend.componentes.reproductor_pasos.textos import formatear_descripcion_html
from src.frontend.controladores.exportacion_pdf.secuencia import seleccionar_intermedios, seleccionar_comprobaciones
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
                renderizar_entrada(_leer_entrada(herramienta, enlace), herramienta)
            reproductor = (getattr(enlace.vista, 'reproductor_pasos', None)
                           or getattr(enlace.vista, 'reproductor', None))
            if reproductor is not None:
                _renderizar_pasos(herramienta, reproductor)
                _renderizar_resultado(herramienta, reproductor, contenedor)
                _renderizar_comprobaciones(herramienta, reproductor)
        yield temporal
    finally:
        if not temporal.is_deleted:
            temporal.delete()


def _region(clave: str):
    return ui.column().classes('w-full gap-4').props(f'data-pdf-captura={clave}')


def _leer_entrada(herramienta: str, enlace) -> dict:
    entrada = enlace.entrada()
    if herramienta == 'matrices':
        matrices = enlace.vista.panel_captura_matrices.obtener_datos_crudos()
        return {**entrada, 'matrices': {nombre: [[valor or '0' for valor in fila] for fila in matriz['datos']]
                                       for nombre, matriz in matrices.items()}}
    return entrada


def _renderizar_pasos(herramienta: str, reproductor) -> None:
    for numero, paso in enumerate(seleccionar_intermedios(reproductor.pasos), 1):
        with _region(f'{herramienta}-paso-{numero}'):
            _renderizar_paso(paso, reproductor)


def _renderizar_paso(paso, reproductor) -> None:
    ui.label(textos.PDF_PASO_ORIGINAL.format(numero=paso.indice + 1,
                                           total=len(reproductor.pasos))).classes('text-h6')
    ui.html(formatear_descripcion_html(paso.descripcion))
    if paso.explicacion and paso.explicacion != paso.descripcion:
        ui.html(formatear_descripcion_html(paso.explicacion))
    cuerpo = ui.column().classes('w-full')
    reproductor.renderizar_cuerpo(paso, cuerpo)


def _renderizar_comprobaciones(herramienta: str, reproductor) -> None:
    if f'{herramienta}-comprobaciones' in textos.PDF_REGIONES_POR_HERRAMIENTA[herramienta]:
        return
    pasos = seleccionar_comprobaciones(reproductor.pasos, herramienta)
    if pasos:
        with _region(f'{herramienta}-verificaciones'):
            for paso in pasos:
                _renderizar_paso(paso, reproductor)


def _renderizar_resultado(herramienta: str, reproductor, contenedor) -> None:
    clave = f'{herramienta}-resultado'
    if clave not in textos.PDF_REGIONES_POR_HERRAMIENTA[herramienta] or not reproductor.pasos:
        return
    if any(elemento._props.get('data-pdf-captura') == clave for elemento in contenedor.descendants()):
        return
    with _region(clave):
        _renderizar_paso(reproductor.pasos[-1], reproductor)
