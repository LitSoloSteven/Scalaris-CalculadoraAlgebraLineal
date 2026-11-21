"""Reutilización acotada de datos derivados de una revisión de captura."""
from collections.abc import Callable
from typing import Any


def reutilizar_captura(vista: Any, nombre: str, clave: tuple, construir: Callable[[], Any]) -> Any:
    """Retiene un derivado por nombre, clave y revisión; sin revisión calcula siempre y propaga errores.
    Los consumidores deben copiar los valores mutables antes de exponerlos."""
    revision = getattr(vista, '_revision_captura', None)
    if revision is None:
        return construir()
    cache = getattr(vista, '_memo_captura', None)
    if cache is None or cache[0] != (revision, clave):
        cache = ((revision, clave), {})
        vista._memo_captura = cache
    if nombre not in cache[1]:
        cache[1][nombre] = construir()
    return cache[1][nombre]
