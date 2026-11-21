"""Datos de presentación de una operación romana."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PresentacionRomana:
    """Agrupa operandos y etiquetas para presentar un resultado romano."""

    operandos: tuple[str, str]
    simbolo: str
    nombre: str
    operacion: str
