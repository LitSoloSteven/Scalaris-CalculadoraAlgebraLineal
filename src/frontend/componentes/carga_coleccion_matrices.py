"""Carga focalizada de una matriz en la colección del editor."""
from typing import Any
from src.frontend.componentes.estado_captura_matrices import crear_registro_matriz


def cargar_matriz_a(panel: Any, datos: list[list[str]]) -> None:
    """Reemplaza A, conserva las demás capturas y notifica una sola edición."""
    panel.matrices["A"] = crear_registro_matriz(datos)
    panel.matrices["A"]["cache"].update({
        (fila, columna): "0" for fila, valores in enumerate(datos)
        for columna, valor in enumerate(valores) if str(valor).strip() == "0"
    })
    panel.renderizar_todas()
    if panel.al_cambiar_datos:
        panel.al_cambiar_datos()
