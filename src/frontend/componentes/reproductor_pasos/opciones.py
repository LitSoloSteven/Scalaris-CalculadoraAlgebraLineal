"""Opciones propias del reproductor y de sus tablas aumentadas."""
from collections.abc import Callable, Sequence
from typing import TypedDict
from .modelo import PasoReproductor


class OpcionesReproductor(TypedDict, total=False):
    """Agrupa la ayuda y las acciones opcionales del reproductor."""

    titulo: str
    lineas_ayuda: Sequence[str]
    tipos_leyenda: Sequence[str]
    al_explicar: Callable[[PasoReproductor], None] | None
    esta_ocupado: Callable[[], bool]


class OpcionesTablaAumentada(TypedDict, total=False):
    """Define resaltados y etiquetas opcionales de una tabla aumentada."""

    filas_cambiadas: Sequence[int]
    pivote: tuple[int, int] | None
    filas_intercambio: Sequence[int]
    bloque_resultado: bool
    etiquetas_izquierda: Sequence[str] | None
    etiquetas_derecha: Sequence[str] | None
