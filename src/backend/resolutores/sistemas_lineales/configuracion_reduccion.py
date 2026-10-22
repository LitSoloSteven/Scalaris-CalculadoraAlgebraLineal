"""Opciones y validaciones del motor de reduccion de filas."""
from dataclasses import dataclass
from math import isfinite

from src.backend.constantes import CERO_EPSILON

ESTRATEGIAS_PIVOTE = ("parcial", "primer_no_nulo", "sin_intercambios")


@dataclass(frozen=True)
class ConfiguracionReduccion:
    """Configura pivoteo, forma reducida, escalamiento y captura de factores exactos."""

    tolerancia_cero: float = CERO_EPSILON
    reduccion_completa: bool = False
    estrategia_pivote: str = "parcial"
    normalizar_pivotes: bool = True
    capturar_multiplicadores: bool = False

    def __post_init__(self) -> None:
        """Rechaza opciones incoherentes mediante ValueError antes de reducir."""
        _validar_tolerancia(self.tolerancia_cero)
        if self.estrategia_pivote not in ESTRATEGIAS_PIVOTE:
            raise ValueError(f"Estrategia de pivote no admitida: {self.estrategia_pivote!r}.")
        if any(type(valor) is not bool for valor in (
            self.reduccion_completa, self.normalizar_pivotes, self.capturar_multiplicadores,
        )):
            raise ValueError("Las opciones de reduccion deben ser booleanas.")
        if self.capturar_multiplicadores and (self.estrategia_pivote != "sin_intercambios" or self.reduccion_completa):
            raise ValueError("Capturar multiplicadores requiere eliminacion progresiva sin intercambios.")


def _validar_tolerancia(tolerancia: float) -> None:
    if type(tolerancia) not in (int, float) or tolerancia < 0 or (isinstance(tolerancia, float) and not isfinite(tolerancia)):
        raise ValueError("La tolerancia de cero debe ser un numero finito no negativo.")
