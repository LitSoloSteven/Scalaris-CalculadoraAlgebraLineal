"""Núcleo compartido para gestión de caché, límites y animación en cuadrículas de matriz."""
from __future__ import annotations

import asyncio
import json
from typing import Any
from nicegui import ui

from src.frontend.constantes import (
    DIMENSION_MAXIMA_INVERSA,
    DIMENSION_MAXIMA_MATRICES,
    DIMENSION_MAXIMA_SISTEMAS,
)

DIMENSION_MINIMA = 1


def purgar_cache_bidimensional(
    cache: dict[tuple[int, int], str], max_filas: int, max_columnas: int
) -> dict[tuple[int, int], str]:
    """Elimina del diccionario de caché las celdas que quedan fuera del nuevo rango."""
    return {(r, c): v for (r, c), v in cache.items() if r < max_filas and c < max_columnas}


def purgar_cache_unidimensional(
    cache: dict[int, str], max_tamano: int
) -> dict[int, str]:
    """Elimina las entradas fuera del tamaño máximo para vectores o términos independientes."""
    return {r: v for r, v in cache.items() if r < max_tamano}


def actualizar_estados_botones_dimension(
    btn_dec: Any, btn_inc: Any, valor_actual: int, minimo: int = DIMENSION_MINIMA, maximo: int = 10
) -> None:
    """Habilita o deshabilita los botones de incremento y decremento según los límites."""
    if btn_dec:
        btn_dec.disable() if valor_actual <= minimo else btn_dec.enable()
    if btn_inc:
        btn_inc.disable() if valor_actual >= maximo else btn_inc.enable()


def props_celda_accesible(
    fila: int,
    columna: int,
    *,
    id_matriz: str | None = None,
    nombre_campo: str | None = None,
) -> str:
    """Construye las propiedades HTML accesibles incluyendo fila y columna para lectores."""
    aria = f'aria-label="Fila {fila + 1}, columna {columna + 1}"'
    base = f'{aria} borderless autocomplete="new-password"'
    if id_matriz:
        base += f' data-matriz-identificador="{id_matriz}" data-matriz-fila="{fila}" data-matriz-columna="{columna}"'
    else:
        base += f' data-ecuaciones-fila="{fila}" data-ecuaciones-columna="{columna}"'
    if nombre_campo:
        base += f' name="{nombre_campo}"'
    return base


def props_vector_accesible(
    indice: int, orientacion: str, *, nombre_vector: str, identificador_panel: str
) -> str:
    """Identifica una componente y su orientación para navegación y pegado vectoriales."""
    es_columna = orientacion == "column"
    propiedades = props_celda_accesible(
        indice if es_columna else 0, 0 if es_columna else indice,
        id_matriz=nombre_vector, nombre_campo=f"{nombre_vector}_{indice}",
    )
    orientacion_cliente = "columna" if es_columna else "fila"
    return (f'{propiedades} data-geometria-vector="{identificador_panel}_{nombre_vector}" '
            f'data-geometria-indice="{indice}" data-geometria-orientacion="{orientacion_cliente}"')


async def animar_salida_cuadricula(
    selector_destino: str,
    *,
    nombre_matriz: str | None = None,
) -> None:
    """Invoca la animación de salida de celdas antes de redimensionar la cuadrícula."""
    await _animar_cuadricula("Salida", selector_destino, nombre_matriz)


async def animar_entrada_cuadricula(
    selector_destino: str, *, nombre_matriz: str | None = None
) -> None:
    """Aplica una pausa breve y dispara la animación de entrada para celdas agregadas."""
    await asyncio.sleep(0.05)
    await _animar_cuadricula("Entrada", selector_destino, nombre_matriz)


async def _animar_cuadricula(accion: str, selector_destino: str, nombre_matriz: str | None) -> None:
    if nombre_matriz:
        argumentos = f"{json.dumps(nombre_matriz)}, {json.dumps(selector_destino)}"
        tipo_destino = "Matriz"
    else:
        argumentos = f"Array.from(document.querySelectorAll({json.dumps(selector_destino)}))"
        tipo_destino = "Celdas"
    codigo = f"return window.scalaris?.cuadricula?.animar{accion}{tipo_destino}({argumentos}) || Promise.resolve();"
    try:
        await ui.run_javascript(codigo)
    except Exception:
        pass
