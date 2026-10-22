"""Avisos compartidos de resultado y orientación ante fallos de presentación."""
from nicegui import ui

MENSAJE_ERROR_INESPERADO = 'Error inesperado. No se pudo completar el cálculo. Revisa los datos e inténtalo de nuevo.'
CLASES_AVISO_ERROR = 'items-center gap-2 px-4 py-2 distintivo-error mb-4 w-fit'


def renderizar_aviso_resultado(mensaje: str, icono: str, clases: str) -> None:
    """Presenta un mensaje como texto y un icono dentro de las clases indicadas."""
    with ui.row().classes(clases):
        ui.icon(icono, size='sm')
        ui.label(mensaje).classes('font-bold')


def mostrar_error_inesperado(contenedor) -> None:
    """Reemplaza el contenido montado por un error orientativo y lo notifica."""
    if contenedor.is_deleted:
        return
    contenedor.clear()
    contenedor.classes(remove='items-center justify-center', add='items-start justify-start')
    with contenedor:
        renderizar_aviso_resultado(MENSAJE_ERROR_INESPERADO, 'close', CLASES_AVISO_ERROR)
    ui.notify(MENSAJE_ERROR_INESPERADO, type='negative', position='top')
