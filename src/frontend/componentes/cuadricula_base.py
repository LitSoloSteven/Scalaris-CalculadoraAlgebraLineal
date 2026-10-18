"""Núcleo compartido para gestión de caché, límites y animación en cuadrículas de matriz."""
from __future__ import annotations

import asyncio
import json
from typing import Any
from nicegui import ui

from src.backend.constantes import DIMENSION_MAXIMA_MATRICES, DIMENSION_MINIMA


def deshabilitar_botones_dimension(botones: tuple[Any, ...]) -> None:
    """Deshabilita los controles presentes mientras se modifica una cuadrícula."""
    for boton in botones:
        if boton:
            boton.disable()


def sincronizar_cache_celdas(entradas: list[list[Any]], cache: dict) -> None:
    """Copia al caché los valores no vacíos de las entradas bidimensionales."""
    for fila, entradas_fila in enumerate(entradas):
        for columna, celda in enumerate(entradas_fila):
            if celda.value:
                cache[(fila, columna)] = celda.value


def cache_matriz_desde_datos(datos: list[list[str]]) -> dict[tuple[int, int], str]:
    """Construye el caché de captura omitiendo las cadenas vacías y los ceros."""
    cache = {}
    for fila, valores in enumerate(datos):
        for columna, valor in enumerate(valores):
            texto = str(valor).strip()
            if texto and texto != "0":
                cache[(fila, columna)] = texto
    return cache


def purgar_cache_bidimensional(
    cache: dict[tuple[int, int], str], maximo_filas: int, maximo_columnas: int
) -> dict[tuple[int, int], str]:
    """Elimina del diccionario de caché las celdas que quedan fuera del nuevo rango."""
    return {(r, c): valor for (r, c), valor in cache.items() if r < maximo_filas and c < maximo_columnas}


def purgar_cache_unidimensional(
    cache: dict[int, str], maximo_tamano: int
) -> dict[int, str]:
    """Elimina las entradas fuera del tamaño máximo para vectores o términos independientes."""
    return {r: valor for r, valor in cache.items() if r < maximo_tamano}


def actualizar_estados_botones_dimension(
    boton_reducir: Any, boton_aumentar: Any, valor_actual: int, minimo: int = DIMENSION_MINIMA, maximo: int = DIMENSION_MAXIMA_MATRICES
) -> None:
    """Habilita o deshabilita los botones de incremento y decremento según los límites."""
    if boton_reducir:
        boton_reducir.disable() if valor_actual <= minimo else boton_reducir.enable()
    if boton_aumentar:
        boton_aumentar.disable() if valor_actual >= maximo else boton_aumentar.enable()


def propiedades_celda_accesible(
    fila: int,
    columna: int,
    *,
    identificador_matriz: str | None = None,
    nombre_campo: str | None = None,
) -> str:
    """Construye las propiedades HTML accesibles incluyendo fila y columna para lectores."""
    aria = f'aria-label="Fila {fila + 1}, columna {columna + 1}"'
    base = f'{aria} borderless autocomplete="new-password"'
    if identificador_matriz:
        base += f' data-matriz-identificador="{identificador_matriz}" data-matriz-fila="{fila}" data-matriz-columna="{columna}"'
    else:
        base += f' data-ecuaciones-fila="{fila}" data-ecuaciones-columna="{columna}"'
    if nombre_campo:
        base += f' name="{nombre_campo}"'
    return base


def propiedades_vector_accesible(
    indice: int, orientacion: str, *, nombre_vector: str, identificador_panel: str
) -> str:
    """Identifica una componente y su orientación para navegación y pegado vectoriales."""
    es_columna = orientacion == "columna"
    propiedades = propiedades_celda_accesible(
        indice if es_columna else 0, 0 if es_columna else indice,
        identificador_matriz=nombre_vector, nombre_campo=f"{nombre_vector}_{indice}",
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


def ubicar_celda_matriz(identificador: str, fila: int, columna: int) -> None:
    """Enfoca una celda mediante la API cliente compartida de captura."""
    argumentos = ", ".join(json.dumps(valor) for valor in (identificador, fila, columna))
    ui.run_javascript(f"window.scalaris.cuadricula.sacudirCelda({argumentos});")


def crear_entradas_matriz(contenedor: Any, dimensiones: tuple[int, int], identificador: str) -> list[list[Any]]:
    """Crea una matriz de controles con coordenadas accesibles para captura y pegado."""
    entradas = []
    contenedor.clear()
    with contenedor:
        for fila in range(dimensiones[0]):
            entradas.append(_crear_entradas_fila(fila, dimensiones[1], identificador))
    return entradas


def _crear_entradas_fila(fila: int, columnas: int, identificador: str) -> list[Any]:
    entradas = []
    with ui.row().classes("gap-1 flex-nowrap"):
        for columna in range(columnas):
            entrada = ui.input(placeholder="0").classes("matriz-entrada w-16 text-center shrink-0")
            entrada.props(propiedades_celda_accesible(fila, columna, identificador_matriz=identificador))
            entradas.append(entrada)
    return entradas
