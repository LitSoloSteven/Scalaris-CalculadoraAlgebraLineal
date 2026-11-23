"""Construcción de figuras Plotly exactas para el análisis de subespacios."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MODO_RESTRICCIONES,
    NOTA_CONJUNTO_VACIO,
    NOTA_DIMENSION_SUPERIOR,
    NOTA_GRAFICA_NO_DISPONIBLE,
)
from src.frontend.presentacion.tema import (
    COLORES_TEXTO_GRAFICOS,
    COLOR_MARCADOR_BORDE,
    COLOR_MARCADOR_CLARO,
    COLOR_SOLUCION,
    PALETA_GRAFICOS,
)
from ._colores_figuras import aplicar_colores_figura
from ._figuras_comunes import disposicion_2d, disposicion_3d
from .figura_subespacios_afin import (
    agregar_flecha_2d,
    agregar_flecha_3d,
    agregar_plano_desde_vectores,
    aplicar_layout_1d,
    calcular_rango_visual,
    interpretar_vectores_visuales,
    preparar_figura_afin,
)


@dataclass(frozen=True)
class ResultadoFiguraSubespacio:
    """Agrupa la figura preparada, su descripción accesible y el motivo si no aplica."""

    disponible: bool
    figura: Any | None
    descripcion: str
    motivo_indisponible: str | None
    es_1d: bool = False


def preparar_figura_subespacio(
    resultado: dict, *, tema: str = "papel"
) -> ResultadoFiguraSubespacio:
    """Genera una figura Plotly en dimensiones 1 a 3 o explica por qué no se grafica."""
    dimension_ambiente = int(resultado.get("dimension_ambiente") or 0)
    descripcion = str(resultado.get("descripcion_geometrica") or "")
    if resultado.get("es_vacio"):
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_CONJUNTO_VACIO)
    if dimension_ambiente > 3:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_DIMENSION_SUPERIOR)
    if dimension_ambiente < 1:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    if resultado.get("clasificacion") == "AFIN_NO_SUBESPACIO":
        figura = preparar_figura_afin(resultado, tema=tema)
        return _resultado_desde_figura(figura, descripcion, dimension_ambiente)
    return _preparar_subespacio_lineal(resultado, dimension_ambiente, descripcion, tema)


def _resultado_desde_figura(
    figura: Any | None, descripcion: str, dimension_ambiente: int
) -> ResultadoFiguraSubespacio:
    if figura is None:
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    return ResultadoFiguraSubespacio(True, figura, descripcion, None, es_1d=dimension_ambiente == 1)


def _preparar_subespacio_lineal(
    resultado: dict, dimension_ambiente: int, descripcion: str, tema: str
) -> ResultadoFiguraSubespacio:
    try:
        fracciones, coordenadas = interpretar_vectores_visuales(resultado.get("base") or (), dimension_ambiente)
    except (OverflowError, ValueError):
        return ResultadoFiguraSubespacio(False, None, descripcion, NOTA_GRAFICA_NO_DISPONIBLE)
    etiquetas = tuple(resultado.get("etiquetas_generadores_base") or ())
    if not etiquetas and resultado.get("modo") == MODO_RESTRICCIONES:
        etiquetas = tuple(f"d_{indice + 1}" for indice in range(len(fracciones)))
    figura = _construir_figura_por_dimension(dimension_ambiente, coordenadas, fracciones, etiquetas, tema)
    return _resultado_desde_figura(figura, descripcion, dimension_ambiente)


def _construir_figura_por_dimension(
    dimension_ambiente: int,
    coordenadas: tuple[tuple[float, ...], ...],
    fracciones: tuple[tuple[Fraction, ...], ...],
    etiquetas: tuple[str, ...],
    tema: str,
):
    import plotly.graph_objects as graficos

    figura = graficos.Figure()
    rango = calcular_rango_visual(coordenadas)
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS["papel"])
    if dimension_ambiente == 1:
        _armar_escena_1d(figura, coordenadas, etiquetas, rango, fuente)
    elif dimension_ambiente == 2:
        _armar_escena_2d(figura, coordenadas, etiquetas, rango)
        disposicion_2d(figura, rango_ejes=rango, color_fuente=fuente, revision="subespacios-2d")
    else:
        if not _armar_escena_3d(figura, coordenadas, fracciones, etiquetas, rango):
            return None
        disposicion_3d(figura, rango_ejes=rango, color_fuente=fuente, revision="subespacios-3d")
    aplicar_colores_figura(figura, tema)
    return figura


def _agregar_origen(figura, dimension: int, *, destacado: bool) -> None:
    import plotly.graph_objects as graficos

    color_relleno = COLOR_SOLUCION if destacado else COLOR_MARCADOR_CLARO
    marcador = dict(color=color_relleno, size=10 if dimension < 3 else 7, line=dict(color=COLOR_MARCADOR_BORDE, width=2))
    coordenadas = dict(x=[0.0], y=[0.0], mode="markers", name="Origen (0)", marker=marcador, hoverinfo="name")
    if dimension == 3:
        coordenadas["z"] = [0.0]
        figura.add_trace(graficos.Scatter3d(**coordenadas))
        return
    figura.add_trace(graficos.Scatter(**coordenadas))


def _etiqueta_base(etiquetas: tuple[str, ...], indice: int) -> str:
    return etiquetas[indice] if indice < len(etiquetas) else f"b_{indice + 1}"


def _armar_escena_1d(figura, coordenadas: tuple, etiquetas: tuple[str, ...], rango: list[float], fuente: str) -> None:
    import plotly.graph_objects as graficos

    figura.add_trace(graficos.Scatter(
        x=rango, y=[0.0, 0.0], mode="lines", name="Eje ℝ¹",
        line=dict(color=COLOR_MARCADOR_BORDE, width=2),
    ))
    if coordenadas:
        figura.add_trace(graficos.Scatter(
            x=rango, y=[0.0, 0.0], mode="lines", name="Subespacio W = ℝ¹",
            line=dict(color=COLOR_SOLUCION, width=6), opacity=0.45,
        ))
        agregar_flecha_2d(figura, (0.0, 0.0), (coordenadas[0][0], 0.0), _etiqueta_base(etiquetas, 0), PALETA_GRAFICOS[0])
    _agregar_origen(figura, 1, destacado=not coordenadas)
    aplicar_layout_1d(figura, rango, fuente)


def _armar_escena_2d(figura, coordenadas: tuple, etiquetas: tuple[str, ...], rango: list[float]) -> None:
    import plotly.graph_objects as graficos

    dimension = len(coordenadas)
    if dimension == 1:
        mayor = max(abs(coordenadas[0][0]), abs(coordenadas[0][1]))
        factor = rango[1] / mayor
        figura.add_trace(graficos.Scatter(
            x=[-coordenadas[0][0] * factor, coordenadas[0][0] * factor],
            y=[-coordenadas[0][1] * factor, coordenadas[0][1] * factor],
            mode="lines", name="Recta generada",
            line=dict(color=COLOR_SOLUCION, width=4), opacity=0.75,
        ))
    elif dimension == 2:
        inicio, fin = rango
        figura.add_trace(graficos.Scatter(
            x=[inicio, fin, fin, inicio, inicio], y=[inicio, inicio, fin, fin, inicio],
            mode="lines", name="Espacio ambiente ℝ²",
            line=dict(color=COLOR_SOLUCION, width=2, dash="dot"), opacity=0.65,
        ))
    for indice, vector in enumerate(coordenadas):
        agregar_flecha_2d(
            figura, (0.0, 0.0), (vector[0], vector[1]),
            _etiqueta_base(etiquetas, indice), PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)],
        )
    _agregar_origen(figura, 2, destacado=dimension == 0)


def _armar_escena_3d(
    figura, coordenadas: tuple, fracciones: tuple, etiquetas: tuple[str, ...], rango: list[float],
) -> bool:
    import plotly.graph_objects as graficos

    dimension = len(coordenadas)
    if dimension == 1:
        _agregar_recta_3d(figura, coordenadas[0], rango)
    elif dimension == 2 and not agregar_plano_desde_vectores(
        figura, (Fraction(0), Fraction(0), Fraction(0)), fracciones, rango, "Plano generado"
    ):
        return False
    elif dimension == 3:
        _agregar_ejes_3d(figura, rango, graficos)
    for indice, vector in enumerate(coordenadas):
        agregar_flecha_3d(
            figura, (0.0, 0.0, 0.0), (vector[0], vector[1], vector[2]),
            _etiqueta_base(etiquetas, indice), PALETA_GRAFICOS[indice % len(PALETA_GRAFICOS)],
        )
    _agregar_origen(figura, 3, destacado=dimension == 0)
    return True


def _agregar_recta_3d(figura, direccion: tuple[float, ...], rango: list[float]) -> None:
    import plotly.graph_objects as graficos

    mayor = max(abs(valor) for valor in direccion)
    factor = rango[1] / mayor
    figura.add_trace(graficos.Scatter3d(
        x=[-direccion[0] * factor, direccion[0] * factor],
        y=[-direccion[1] * factor, direccion[1] * factor],
        z=[-direccion[2] * factor, direccion[2] * factor],
        mode="lines", name="Recta generada", line=dict(color=COLOR_SOLUCION, width=4), opacity=0.8,
    ))


def _agregar_ejes_3d(figura, rango: list[float], graficos) -> None:
    ejes = ((rango, [0.0, 0.0], [0.0, 0.0]), ([0.0, 0.0], rango, [0.0, 0.0]), ([0.0, 0.0], [0.0, 0.0], rango))
    for indice, (eje_x, eje_y, eje_z) in enumerate(ejes):
        figura.add_trace(graficos.Scatter3d(
            x=eje_x, y=eje_y, z=eje_z, mode="lines",
            name="Ejes de ℝ³", showlegend=indice == 0,
            line=dict(color=COLOR_MARCADOR_BORDE, width=2, dash="dot"),
        ))
