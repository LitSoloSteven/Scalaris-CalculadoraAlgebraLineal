"""Componentes reutilizables de UI de Scalaris."""

from .panel_ia import PanelIA
from .estructura_aplicacion import crear_estructura_aplicacion
from .calculadora import PanelCalculadora
from .cuadricula_ecuaciones import CuadriculaEcuaciones
from .captura_matrices import PanelCapturaMatrices
from .barra_navegacion import crear_barra_navegacion
from .panel_matriz_cuadrada import PanelMatrizCuadrada
from .captura_vectores import PanelCapturaVectores

__all__ = [
    "PanelIA",
    "PanelCalculadora",
    "CuadriculaEcuaciones",
    "PanelCapturaMatrices",
    "PanelMatrizCuadrada",
    "PanelCapturaVectores",
    "crear_estructura_aplicacion",
    "crear_barra_navegacion",
]
