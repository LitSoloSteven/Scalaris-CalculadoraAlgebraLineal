"""Exportación del submódulo de operaciones vectoriales."""

from src.backend.resolutores.operaciones_vectores.combinacion_lineal import (
    ResolutorCombinacionLineal,
)
from src.backend.resolutores.operaciones_vectores.operaciones import (
    ResolutorOperacionesVectores,
)

__all__ = [
    "ResolutorOperacionesVectores",
    "ResolutorCombinacionLineal",
]
