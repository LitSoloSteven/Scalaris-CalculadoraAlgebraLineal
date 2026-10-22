"""Actualización del borde de una cuadrícula rectangular con respaldo completo."""
from collections.abc import Callable
from typing import Any


def actualizar_rectangulo(
    estado: dict, anterior: tuple[int, int], actual: tuple[int, int],
    crear_fila: Callable[[int], None], crear_celda: Callable[[int, int], Any],
) -> bool:
    """Conserva el interior según registros, dimensiones y constructores; indica si requiere respaldo.
    Propaga errores de creación para permitir la recuperación en el siguiente cambio."""
    filas, columnas = anterior
    nuevas_filas, nuevas_columnas = actual
    entradas, contenedores = estado['entradas'], estado.get('filas_interfaz', [])
    if abs(nuevas_filas - filas) + abs(nuevas_columnas - columnas) != 1:
        return False
    if not _estructura_completa(estado, anterior):
        return False
    if nuevas_filas < filas:
        contenedores.pop().delete()
        entradas.pop()
    elif nuevas_filas > filas:
        with estado['contenido']:
            crear_fila(filas)
    elif nuevas_columnas < columnas:
        for fila in entradas:
            fila.pop().delete()
    else:
        for indice, fila in enumerate(entradas):
            with contenedores[indice]:
                fila.append(crear_celda(indice, columnas))
    return True


def _estructura_completa(estado: dict, dimensiones: tuple[int, int]) -> bool:
    filas, columnas = dimensiones
    entradas, contenedores = estado['entradas'], estado.get('filas_interfaz', [])
    return (bool(estado.get('contenido')) and not estado['contenido'].is_deleted
            and len(entradas) == len(contenedores) == filas
            and all(len(fila) == columnas for fila in entradas)
            and all(not fila.is_deleted for fila in contenedores))
