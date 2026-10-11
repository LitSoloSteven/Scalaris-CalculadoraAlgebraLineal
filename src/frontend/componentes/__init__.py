"""Componentes reutilizables de UI de Scalaris."""

from .ai_panel import AIPanel
from .app_shell import create_app_shell
from .calculator import CalculatorPanel
from .equation_grid import EquationGrid
from .matrix_capture import MatrixCapturePanel
from .navbar import create_navbar
from .square_matrix_panel import SquareMatrixPanel
from .vector_capture import VectorCapturePanel

__all__ = [
    "AIPanel",
    "CalculatorPanel",
    "EquationGrid",
    "MatrixCapturePanel",
    "SquareMatrixPanel",
    "VectorCapturePanel",
    "create_app_shell",
    "create_navbar",
]
