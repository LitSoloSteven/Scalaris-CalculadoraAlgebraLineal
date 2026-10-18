"""Representación Plotly de pares vectoriales y sus cuadros precalculados."""
from __future__ import annotations

from typing import Any
from src.frontend.tema import PALETA_GRAFICOS, COLORES_TEXTO_GRAFICOS
from ._figuras_comunes import disposicion_2d, disposicion_3d


def _flecha_3d(figura, extremos: tuple, nombre: str, estilo: dict):
    import plotly.graph_objects as graficos
    inicio, fin = extremos
    figura.add_trace(graficos.Scatter3d(
        x=[inicio[0], fin[0]], y=[inicio[1], fin[1]], z=[inicio[2], fin[2]],
        mode='lines', name=nombre, line=estilo,
    ))
    figura.add_trace(graficos.Scatter3d(
        x=[fin[0]], y=[fin[1]], z=[fin[2]], mode='markers', name=nombre,
        showlegend=False, marker=dict(size=5, color=estilo['color']),
    ))


def _extraer_datos_cuadro(resultado: dict, indice: int | None) -> tuple[list, list, str]:
    estatico = resultado.get('estatica', {})
    vector = estatico.get('vector_u', [])
    suma = estatico.get('u_mas_v', [])
    cuadros = resultado.get('cuadros', [])
    if indice is not None and 0 <= indice < len(cuadros):
        cuadro = cuadros[indice]
        return cuadro.get('escalar_por_u', vector), cuadro.get('escalar_por_u_mas_v', suma), cuadro.get('escalar_exacto', 'k')
    return vector, suma, '1'


def _trazar_vector_2d(figura, coordenadas: list, nombre: str, estilo: dict):
    import plotly.graph_objects as graficos
    figura.add_trace(graficos.Scatter(
        x=[0, coordenadas[0]], y=[0, coordenadas[1]], mode='lines+markers', name=nombre,
        line=estilo, marker=dict(size=[0, 10], symbol=['circle', 'arrow'], angleref='previous'),
    ))


def _trazar_vectores(figura, datos: tuple, dimension: int):
    vector, segundo, suma, etiqueta = datos
    nombres = (f'k·u (k={etiqueta})', 'v', 'k·u + v')
    for indice, (coordenadas, nombre) in enumerate(zip((vector, segundo, suma), nombres)):
        estilo = dict(color=PALETA_GRAFICOS[indice], width=3 if dimension == 2 else 4)
        if indice == 2:
            estilo['dash'] = 'dash'
        if dimension == 2:
            _trazar_vector_2d(figura, coordenadas, nombre, estilo)
        elif dimension == 3:
            _flecha_3d(figura, ([0, 0, 0], coordenadas), nombre, estilo)


def construir_figura_vectores(resultado: dict, *, tema: str = 'papel', indice_cuadro: int | None = None) -> Any:
    """Representa vectores de un resultado o un cuadro ya calculado por el backend."""
    import plotly.graph_objects as graficos
    figura = graficos.Figure()
    dimension = resultado.get('numero_variables', 2)
    rango = resultado.get('rango', [-5, 5])
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS['papel'])
    segundo = resultado.get('estatica', {}).get('vector_v', [])
    vector, suma, etiqueta = _extraer_datos_cuadro(resultado, indice_cuadro)
    if dimension in (2, 3) and vector and segundo and suma:
        _trazar_vectores(figura, (vector, segundo, suma, etiqueta), dimension)
    if dimension == 2:
        disposicion_2d(figura, rango_ejes=rango, color_fuente=fuente, revision='vectores')
    elif dimension == 3:
        disposicion_3d(figura, rango_ejes=rango, color_fuente=fuente, revision='vectores')
    return figura
