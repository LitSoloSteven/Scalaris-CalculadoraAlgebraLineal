"""Límite común de presentación LaTeX para capturas cuadradas."""
from src.backend.constantes import DIMENSION_MAXIMA_LATEX_INVERSA
from src.frontend.textos import VISTA_PREVIA_LIMITE


def orientacion_limite_previa(dimension: int) -> dict | None:
    """Devuelve orientación por encima del límite; dentro de él devuelve None."""
    if dimension > DIMENSION_MAXIMA_LATEX_INVERSA:
        return {'estado': 'limite', 'mensaje': VISTA_PREVIA_LIMITE.format(
            dimension=DIMENSION_MAXIMA_LATEX_INVERSA)}
    return None
