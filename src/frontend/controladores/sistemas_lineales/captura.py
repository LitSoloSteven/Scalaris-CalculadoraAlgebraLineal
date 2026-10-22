"""Delegación de captura y serialización de vistas previas de sistemas."""
from src.backend.resolutores.sistemas_lineales.captura_ecuaciones import preparar_ecuaciones
from src.backend.resolutores.sistemas_lineales import vista_previa


def preparar_captura_ecuaciones(lineas: list[str]) -> dict:
    """Delega el análisis y devuelve datos de captura serializables."""
    return preparar_ecuaciones(lineas)


def preparar_vista_previa(captura: dict) -> dict:
    """Devuelve únicamente estado, mensaje y LaTeX listos para renderizar."""
    return vista_previa.preparar_vista_previa(captura)
