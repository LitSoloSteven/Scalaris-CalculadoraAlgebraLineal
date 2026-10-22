"""Configuración de límites y orientación para la captura de vectores."""
from typing import TypedDict


class OpcionesCapturaVectores(TypedDict, total=False):
    """Agrupa las restricciones opcionales del panel de vectores."""

    minimo_vectores: int
    maximo_vectores: int
    permitir_orientacion: bool
    orientacion_inicial: str
    etiqueta_primer_vector: str | None
