"""Representación de vectores columna, objetivo y sumas parciales ya resueltas."""
from __future__ import annotations

from typing import Any
from src.frontend.tema import PALETA_GRAFICOS, COLOR_MARCADOR_CLARO, COLOR_MARCADOR_BORDE, COLORES_TEXTO_GRAFICOS
from ._figuras_comunes import disposicion_2d, disposicion_3d
from ._colores_figuras import aplicar_colores_figura


def _datos_segmento(inicio: list, fin: list, dimension: int) -> dict:
    datos = dict(x=[inicio[0], fin[0]], y=[inicio[1], fin[1]])
    if dimension == 3:
        datos['z'] = [inicio[2], fin[2]]
    return datos


def _agregar_traza(figura, datos: dict, dimension: int):
    import plotly.graph_objects as graficos
    constructor = graficos.Scatter if dimension == 2 else graficos.Scatter3d
    figura.add_trace(constructor(**datos))


def _dibujar_columnas(figura, vectores: list, dimension: int):
    for indice, vector in enumerate(vectores):
        datos = _datos_segmento([0] * dimension, vector.get('aproximado', []), dimension)
        datos.update(mode='lines+markers' if dimension == 2 else 'lines', name=f'v_{indice + 1}',
                     line=dict(color=PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)], width=2 if dimension == 2 else 3, dash='dot'))
        if dimension == 2:
            datos['marker'] = dict(size=[0, 8], symbol=['circle', 'arrow'], angleref='previous')
        _agregar_traza(figura, datos, dimension)


def _dibujar_objetivo(figura, resultado: dict, dimension: int):
    coordenadas = resultado.get('objetivo', {}).get('aproximado', [])
    if not coordenadas:
        return
    color = COLOR_MARCADOR_CLARO
    if dimension == 2 and resultado.get('objetivo_fuera_del_espacio_generado', False):
        color = PALETA_GRAFICOS[len(resultado.get('vectores', [])) % len(PALETA_GRAFICOS)]
    datos = dict(x=[coordenadas[0]], y=[coordenadas[1]], mode='markers', name='b',
                 marker=dict(color=color, size=12 if dimension == 2 else 6,
                             line=dict(color=COLOR_MARCADOR_BORDE, width=2)))
    if dimension == 3:
        datos['z'] = [coordenadas[2]]
    _agregar_traza(figura, datos, dimension)


def _dibujar_cadena(figura, cadena: list, dimension: int):
    anterior = [0] * dimension
    for indice, paso in enumerate(cadena or []):
        coordenadas = paso.get('aproximado', [])
        datos = _datos_segmento(anterior, coordenadas, dimension)
        datos.update(mode='lines', name=paso.get('etiqueta', ''),
                     line=dict(color=PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)], width=3 if dimension == 2 else 4))
        _agregar_traza(figura, datos, dimension)
        anterior = coordenadas


def construir_figura_combinacion(resultado: dict, *, tema: str = 'papel') -> Any:
    """Representa la combinación y las sumas parciales del resultado de dominio."""
    import plotly.graph_objects as graficos
    figura = graficos.Figure()
    dimension = resultado.get('numero_variables', 2)
    if dimension not in (2, 3):
        return figura
    _dibujar_columnas(figura, resultado.get('vectores', []), dimension)
    _dibujar_objetivo(figura, resultado, dimension)
    _dibujar_cadena(figura, resultado.get('cadena'), dimension)
    disposicion = disposicion_2d if dimension == 2 else disposicion_3d
    disposicion(figura, rango_ejes=resultado.get('rango', [-5, 5]),
                color_fuente=COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS['papel']), revision='combinacion')
    aplicar_colores_figura(figura, tema)
    return figura
