"""Constantes de configuración para la vista de Determinantes."""
from __future__ import annotations

from src.frontend.controllers.determinant_ops._config import LATEX_MAX_N

PREVIEW_MAX_N: int = LATEX_MAX_N
AI_CONTEXT_MAX_N: int = 12
CONFIRMAR_N_GRANDE: int = 20
HISTORIAL_MAX: int = 5
ID_RESULTADOS: str = "resultados-det"
ID_BOTON_LIMPIAR: str = "btn-limpiar-main"
