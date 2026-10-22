"""Captura de una ventana matricial y recuento de celdas inválidas."""
from collections.abc import Callable, Sequence
from typing import Any


def extraer_ventana_matriz(
    filas: Sequence[Sequence[Any]],
    total_columnas: int,
    ventana: tuple[int, int],
    formatear_celda: Callable[[str], str],
    es_invalida: Callable[[str], bool],
) -> tuple[list[list[str]], int]:
    """Devuelve celdas visibles y errores totales; las filas irregulares conservan IndexError."""
    filas_visibles, columnas_visibles = ventana
    datos, invalidos = [], 0
    for i in range(len(filas)):
        fila_datos = []
        for j in range(total_columnas):
            valor = str(filas[i][j]).strip()
            if es_invalida(valor):
                invalidos += 1
            if i < filas_visibles and j < columnas_visibles:
                fila_datos.append(formatear_celda(valor))
        if i < filas_visibles:
            datos.append(fila_datos)
    return datos, invalidos
