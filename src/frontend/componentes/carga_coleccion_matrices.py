"""Carga focalizada de una matriz en la colección del editor."""
from typing import Any
from src.frontend.componentes.estado_captura_matrices import crear_registro_matriz


def cargar_matriz_a(panel: Any, datos: list[list[str]]) -> None:
    """Reemplaza A, conserva las demás capturas y notifica una sola edición."""
    panel.matrices["A"] = crear_registro_matriz(datos)
    panel.renderizar_todas()
    if panel.al_cambiar_datos:
        panel.al_cambiar_datos()
