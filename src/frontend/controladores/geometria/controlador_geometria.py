"""Fachada y controlador principal para el visualizador geométrico interactivo."""
from src.frontend.controladores.geometria.controlador_combinacion import (
    procesar_combinacion,
)
from src.frontend.controladores.geometria.controlador_rectas_planos import (
    procesar_rectas_planos,
)
from src.frontend.controladores.geometria.controlador_vectores import (
    procesar_vectores,
)
from src.frontend.controladores.geometria.utilidades import selector_celda_error


class ControladorGeometria:
    """Controlador que delega la visualización geométrica a módulos especializados."""

    procesar_rectas_planos = staticmethod(procesar_rectas_planos)
    procesar_vectores = staticmethod(procesar_vectores)
    procesar_combinacion = staticmethod(procesar_combinacion)


__all__ = [
    "ControladorGeometria",
    "selector_celda_error",
]
