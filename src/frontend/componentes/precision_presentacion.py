"""Validación y comunicación del formato numérico de los resultados."""
from nicegui import ui

from src.frontend.controladores.biseccion.captura_criterio import precision_presentacion


def leer_precision_presentacion(campo: ui.number, error: ui.label) -> int | None:
    """Devuelve la precisión válida del campo o None y actualiza su mensaje de error."""
    try:
        precision = precision_presentacion(campo.value)
    except ValueError as fallo:
        error.set_text(str(fallo))
        return None
    error.set_text("")
    return precision
