"""Componentes reutilizables de UI de Scalaris."""

from .panel_ia import PanelIA
from .aplicacion.controles.estructura_aplicacion import crear_estructura_aplicacion
from .captura.paneles.calculadora import PanelCalculadora
from .captura.ecuaciones.cuadricula_ecuaciones import CuadriculaEcuaciones
from .captura.matrices.captura_matrices import PanelCapturaMatrices
from .aplicacion.controles.barra_navegacion import crear_barra_navegacion
from .captura.paneles.panel_matriz_cuadrada import PanelMatrizCuadrada
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
