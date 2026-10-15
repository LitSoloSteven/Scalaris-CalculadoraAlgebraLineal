"""Constantes de configuración para el controlador de determinantes."""
from __future__ import annotations

from src.backend.constants import (
    COFACTOR_MAX_DIMENSION,
    INVERSE_LATEX_MAX_DIMENSION,
    INVERSE_MAX_DIMENSION,
)

METODOS: tuple[str, str] = ("cofactores", "lu")
METODO_COFACTORES, METODO_LU = METODOS

COFACTORES_MAX_N: int = COFACTOR_MAX_DIMENSION

# LU también reduce [A | I], igual que la inversa.
LU_MAX_N: int = INVERSE_MAX_DIMENSION

LATEX_MAX_N: int = INVERSE_LATEX_MAX_DIMENSION

ETIQUETAS_METODO: dict[str, str] = {
    METODO_COFACTORES: "Cofactores",
    METODO_LU: "Eliminación con pivoteo",
}
