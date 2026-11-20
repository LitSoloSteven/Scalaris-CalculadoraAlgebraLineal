"""Datos canónicos para destacar Sistemas de ecuaciones en la portada."""
from src.frontend.navegacion import ElementoNavegacion, elementos_navegacion, pilar_de
from src.frontend.controladores.inicio._recientes import IDENTIFICADOR_DESTACADA_PREDETERMINADA


def acceso_destacado() -> ElementoNavegacion:
    """Devuelve el acceso de Sistemas que comparten el destacado y el ejemplo."""
    identificador = IDENTIFICADOR_DESTACADA_PREDETERMINADA
    return next(
        acceso for acceso in elementos_navegacion(pilar_de(identificador).identificador)
        if acceso.clave == identificador
    )
