"""Datos canónicos para destacar Sistemas de ecuaciones en la portada."""
from src.frontend.navegacion import Herramienta, herramienta_por_identificador
from src.frontend.controladores.inicio._recientes import IDENTIFICADOR_DESTACADA_PREDETERMINADA


def acceso_destacado() -> Herramienta:
    """Devuelve el acceso de Sistemas que comparten el destacado y el ejemplo."""
    return herramienta_por_identificador(IDENTIFICADOR_DESTACADA_PREDETERMINADA)
