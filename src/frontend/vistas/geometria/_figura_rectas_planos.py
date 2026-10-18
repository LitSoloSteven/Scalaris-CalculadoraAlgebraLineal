"""Representación Plotly de rectas, planos y conjuntos solución ya resueltos."""
from __future__ import annotations

from typing import Any
from src.backend.geometria.muestreo import extremos_recta, superficie_plano
from src.frontend.tema import (
    PALETA_GRAFICOS, COLOR_MARCADOR_CLARO, COLOR_MARCADOR_BORDE, COLORES_TEXTO_GRAFICOS, COLOR_SOLUCION,
)
from ._figuras_comunes import disposicion_2d, disposicion_3d


def _trazar_solucion_2d(figura, conjunto: dict | None, color: str):
    import plotly.graph_objects as graficos
    if not conjunto or conjunto.get('tipo') not in ('RECTA', 'PLANO') or conjunto.get('espacio_completo'):
        return
    segmento = conjunto.get('segmento')
    if segmento:
        figura.add_trace(graficos.Scatter(
            x=[segmento[0][0], segmento[1][0]], y=[segmento[0][1], segmento[1][1]],
            mode='lines', name='Conjunto solución (recta)', line=dict(color=color, width=10),
            opacity=0.95, hovertext=conjunto.get('parametros_latex', ''), hoverinfo='text',
        ))


def _trazar_ecuaciones_2d(figura, ecuaciones: list, rango: list):
    import plotly.graph_objects as graficos
    for ecuacion in ecuaciones:
        if ecuacion['tipo'] in ('trivial', 'contradiccion'):
            continue
        extremos = extremos_recta(ecuacion['coeficientes'], ecuacion['objetivo'], rango)
        if extremos is None:
            continue
        indice = ecuacion['indice']
        figura.add_trace(graficos.Scatter(
            x=extremos[0], y=extremos[1], mode='lines', name=f'Ecuación {indice + 1}',
            line=dict(color=PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)], width=3),
        ))


def _trazar_punto(figura, conjunto: dict | None, dimension: int):
    import plotly.graph_objects as graficos
    if not conjunto or conjunto.get('tipo') != 'PUNTO' or not conjunto.get('punto'):
        return
    punto = conjunto['punto']
    exacto = conjunto.get('punto_exacto', [])
    texto = f'({", ".join(exacto)})' if exacto else f'({", ".join(map(str, punto))})'
    datos = dict(
        x=[punto[0]], y=[punto[1]], mode='markers', name='Solución',
        marker=dict(color=COLOR_MARCADOR_CLARO, size=12 if dimension == 2 else 8,
                    line=dict(color=COLOR_MARCADOR_BORDE, width=2)),
        hovertext=texto, hoverinfo='text',
    )
    if dimension == 3:
        datos['z'] = [punto[2]]
    constructor = graficos.Scatter if dimension == 2 else graficos.Scatter3d
    figura.add_trace(constructor(**datos))


def _trazar_superficie(figura, plano: dict, rango: list, estilo: dict):
    import plotly.graph_objects as graficos
    coordenadas = superficie_plano(plano['coeficientes'], plano['termino'], rango)
    if coordenadas is None:
        return
    figura.add_trace(graficos.Surface(
        x=coordenadas[0], y=coordenadas[1], z=coordenadas[2], name=estilo['nombre'], showscale=False,
        opacity=estilo['opacidad'], colorscale=[[0, estilo['color']], [1, estilo['color']]],
    ))


def _trazar_recta_solucion_3d(figura, conjunto: dict, segmento: list):
    import plotly.graph_objects as graficos
    figura.add_trace(graficos.Scatter3d(
        x=[segmento[0][0], segmento[1][0]], y=[segmento[0][1], segmento[1][1]],
        z=[segmento[0][2], segmento[1][2]], mode='lines', name='Conjunto solución (recta)',
        line=dict(color=COLOR_SOLUCION, width=8), opacity=0.95,
        hovertext=conjunto.get('parametros_latex', ''), hoverinfo='text',
    ))


def _trazar_solucion_3d(figura, conjunto: dict | None, rango: list):
    if not conjunto or conjunto.get('tipo') not in ('RECTA', 'PLANO') or conjunto.get('espacio_completo'):
        return
    if conjunto.get('dimension') == 1 and conjunto.get('segmento'):
        _trazar_recta_solucion_3d(figura, conjunto, conjunto['segmento'])
    elif conjunto.get('dimension') == 2 and conjunto.get('normal') and conjunto.get('desplazamiento') is not None:
        plano = {'coeficientes': conjunto['normal'], 'termino': conjunto['desplazamiento']}
        estilo = {'color': COLOR_SOLUCION, 'nombre': 'Conjunto solución (plano)', 'opacidad': 0.95}
        _trazar_superficie(figura, plano, rango, estilo)


def _figura_rectas_2d(figura, resultado: dict, rango: list, fuente: str):
    conjunto = resultado.get('conjunto_solucion')
    _trazar_solucion_2d(figura, conjunto, COLOR_SOLUCION)
    _trazar_ecuaciones_2d(figura, resultado.get('ecuaciones', []), rango)
    _trazar_punto(figura, conjunto, 2)
    disposicion_2d(figura, rango_ejes=rango, color_fuente=fuente, revision='rectas')


def _figura_planos_3d(figura, resultado: dict, rango: list, fuente: str):
    conjunto = resultado.get('conjunto_solucion')
    _trazar_solucion_3d(figura, conjunto, rango)
    for ecuacion in resultado.get('ecuaciones', []):
        if ecuacion['tipo'] in ('trivial', 'contradiccion'):
            continue
        indice = ecuacion['indice']
        plano = {'coeficientes': ecuacion['coeficientes'], 'termino': ecuacion['objetivo']}
        estilo = {'color': PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)],
                  'nombre': f'Ecuación {indice + 1}', 'opacidad': 0.7}
        _trazar_superficie(figura, plano, rango, estilo)
    _trazar_punto(figura, conjunto, 3)
    disposicion_3d(figura, rango_ejes=rango, color_fuente=fuente, revision='planos')


def construir_figura_rectas_planos(resultado: dict, *, tema: str = 'papel') -> Any:
    """Construye la representación del resultado; requiere Plotly instalado."""
    import plotly.graph_objects as graficos
    figura = graficos.Figure()
    dimension = resultado.get('numero_variables', 2)
    rango = resultado.get('rango', [-5, 5])
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS['papel'])
    if dimension == 2:
        _figura_rectas_2d(figura, resultado, rango, fuente)
    elif dimension == 3:
        _figura_planos_3d(figura, resultado, rango, fuente)
    return figura
