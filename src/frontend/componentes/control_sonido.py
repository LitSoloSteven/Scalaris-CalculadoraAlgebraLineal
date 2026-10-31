"""Control de silencio accesible sincronizado por el recurso cliente compartido."""
from nicegui import ui

from src.frontend.componentes.iconos import icono_svg


def renderizar_control_sonido() -> ui.element:
    """Crea un botón de silencio nativo; el cliente persiste y anuncia su estado pulsado."""
    with ui.element('button').classes('boton-icono p-0 texto-principal').props(
        'type="button" data-sonido-control aria-label="Silenciar sonidos" '
        'aria-pressed="false" title="Silenciar sonidos"'
    ) as boton:
        ui.html(icono_svg('sonido')).props('data-sonido-icono="activo" aria-hidden="true"')
        ui.html(icono_svg('sonido_silenciado')).props('data-sonido-icono="silenciado" aria-hidden="true" hidden')
    return boton
