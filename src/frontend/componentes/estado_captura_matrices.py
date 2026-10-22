"""Registros de captura y nombres permanentes de la coleccion matricial."""
from typing import Any

from src.frontend.componentes.cuadricula_base import cache_matriz_desde_datos

MATRICES_PERMANENTES = ("A", "B")
DIMENSION_INICIAL = 3


def crear_registro_matriz(datos: list[list[str]] | None = None) -> dict[str, Any]:
    """Crea un registro de captura vacio o cargado, sin interpretar sus valores."""
    filas = DIMENSION_INICIAL if datos is None else len(datos)
    columnas = len(datos[0]) if datos else DIMENSION_INICIAL
    return {
        "filas": filas, "columnas": columnas, "entradas": [],
        "cache": cache_matriz_desde_datos(datos) if datos is not None else {}, "contenedor": None,
        "etiqueta_filas": None, "etiqueta_dimension": None, "etiqueta_dimension_matriz": None,
        "boton_quitar_fila": None, "boton_agregar_fila": None,
        "boton_quitar_columna": None, "boton_agregar_columna": None,
    }


def asegurar_matrices_permanentes(matrices: dict[str, dict[str, Any]]) -> None:
    """Completa solo los nombres permanentes ausentes sin reemplazar datos existentes."""
    for nombre in MATRICES_PERMANENTES:
        if nombre not in matrices:
            matrices[nombre] = crear_registro_matriz()
