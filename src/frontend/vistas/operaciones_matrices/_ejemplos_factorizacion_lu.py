"""Datos de ejemplo para explorar la factorización PA = LU."""

EJEMPLOS_FACTORIZACION_LU = (
    {"nombre": "Sin intercambios", "descripcion": "Ejemplo sin intercambios de filas.", "datos": [[6, 2, 1], [2, 5, 1], [1, 1, 4]]},
    {"nombre": "Con intercambios", "descripcion": "Ejemplo que requiere intercambiar filas.", "datos": [[1, 2, 3], [4, 5, 6], [7, 8, 10]]},
    {"nombre": "Singular", "descripcion": "Ejemplo de matriz singular.", "datos": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]},
    {"nombre": "Rectangular", "descripcion": "Ejemplo de dos filas y tres columnas.", "datos": [[1, 2, 3], [4, 5, 6]]},
)
