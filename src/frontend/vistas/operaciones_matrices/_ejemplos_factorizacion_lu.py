"""Datos de ejemplo para explorar la factorización PA = LU."""
from src.frontend.textos import LU_EJEMPLOS_TEXTOS

_MATRICES = ([[6, 2, 1], [2, 5, 1], [1, 1, 4]], [[1, 2, 3], [4, 5, 6], [7, 8, 10]],
             [[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 2, 3], [4, 5, 6]])
EJEMPLOS_FACTORIZACION_LU = tuple(
    {"nombre": nombre, "descripcion": descripcion, "datos": matriz}
    for (nombre, descripcion), matriz in zip(LU_EJEMPLOS_TEXTOS, _MATRICES)
)
