"""Invalidación común de solicitudes independientes de bisección."""
from src.frontend.controladores.actualizacion_cancelable import cancelar_actualizacion


def invalidar_panel(panel) -> None:
    """Avanza la revisión, cancela la espera y retira la respuesta de un panel asíncrono."""
    panel._revision_captura += 1
    panel._identificador_calculo += 1
    cancelar_actualizacion(panel.tarea)
    panel.tarea = None
    panel.respuesta = None
