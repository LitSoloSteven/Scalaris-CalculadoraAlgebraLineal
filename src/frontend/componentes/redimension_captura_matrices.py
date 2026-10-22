"""Construcción de filas y celdas de las matrices con nombre."""
from typing import Any
from nicegui import ui
from .cuadricula_base import propiedades_celda_accesible


def crear_celda_matriz(panel: Any, nombre: str, coordenada: tuple[int, int]) -> ui.input:
    """Crea una entrada con el valor y los atributos de la coordenada recibida."""
    fila, columna = coordenada
    valor = panel.matrices[nombre]['cache'].get(coordenada, '')
    propiedades = propiedades_celda_accesible(fila, columna, identificador_matriz=nombre,
                                              nombre_campo=f'{nombre}_r{fila}c{columna}')
    return ui.input(value=valor, placeholder='', on_change=lambda evento: panel._al_cambiar_celda(
        nombre, fila, columna, evento.value)).classes(panel.clases_celda).props(propiedades)


def crear_fila_matriz(panel: Any, nombre: str, indice: int) -> None:
    """Añade una fila al contenido actual y registra sus entradas y contenedor."""
    matriz = panel.matrices[nombre]
    with ui.row().classes('items-center gap-2 mb-2 no-wrap').props(f'data-cuadricula-fila="{nombre}_{indice}"') as fila:
        entradas = [crear_celda_matriz(panel, nombre, (indice, columna)) for columna in range(matriz['columnas'])]
    matriz.setdefault('filas_interfaz', []).append(fila)
    matriz['entradas'].append(entradas)
