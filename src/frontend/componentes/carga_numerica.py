"""Saneamiento de matrices externas con aviso único por carga."""
from src.frontend.componentes.sonido import notificar

from src.frontend.componentes.portapapeles_matricial import filtrar_matriz_numerica
from src.frontend.textos import MENSAJE_ENTRADA_NUMERICA


def preparar_matriz_numerica(datos: list[list[str]]) -> list[list[str]]:
    """Devuelve celdas filtradas y avisa si retiró caracteres distintos de espacios externos."""
    filtrados = filtrar_matriz_numerica(datos)
    if filtrados != [[str(valor).strip() for valor in fila] for fila in datos]:
        notificar(MENSAJE_ENTRADA_NUMERICA, type="warning")
    return filtrados
