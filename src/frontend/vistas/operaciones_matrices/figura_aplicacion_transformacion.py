"""Figuras de aplicación lineal con decimales del dominio y etiquetas exactas."""
from html import escape
import math

import plotly.graph_objects as graficos

from src.frontend import textos_transformaciones as textos
from src.frontend.tema import PALETA_GRAFICOS, COLORES_TEXTO_GRAFICOS
from src.frontend.vistas.geometria._colores_figuras import aplicar_colores_figura
from src.frontend.vistas.geometria._figuras_comunes import disposicion_2d, disposicion_3d


def preparar_escenas_aplicacion(resultado: dict, tipo_objeto: str, *, tema: str = "papel") -> dict:
    """Devuelve escenas comparables o un motivo de omisión, sin recalcular Av."""
    if resultado.get("estado") != "EXITO" or resultado.get("verificacion") is not True:
        return {"escenas": [], "mensaje": textos.GRAFICA_SIN_VERIFICAR}
    dimensiones = (resultado["dimension_dominio"], resultado["dimension_codominio"])
    if any(dimension not in (2, 3) for dimension in dimensiones):
        return {"escenas": [], "mensaje": textos.GRAFICA_DIMENSIONES}
    series = _preparar_series(resultado, tipo_objeto)
    if not _series_dibujables(series, dimensiones):
        return {"escenas": [], "mensaje": textos.GRAFICA_NO_REPRESENTABLE}
    rango = _rango_comun(series)
    if rango is None:
        return {"escenas": [], "mensaje": textos.GRAFICA_NO_REPRESENTABLE}
    grupos = [series] if dimensiones[0] == dimensiones[1] else [[serie] for serie in series]
    escenas = [_construir_escena(grupo, rango, tipo_objeto, tema) for grupo in grupos]
    return {"escenas": escenas, "mensaje": textos.GRAFICA_APROXIMADA}


def _preparar_series(resultado: dict, tipo_objeto: str) -> list[dict]:
    titulos = textos.TITULOS_COORDENADAS[tipo_objeto]
    return [dict(resultado[clave], nombre=titulo, indice=indice)
            for indice, (clave, titulo) in enumerate(zip(
                ("vector_original", "vector_transformado"), titulos))]


def _coordenadas_dibujables(serie: dict, dimension: int) -> bool:
    valores, exactas = serie.get("aproximado", []), serie.get("exacta", [])
    if len(valores) != dimension or len(exactas) != dimension:
        return False
    return all(_componente_dibujable(valor, exacta) for valor, exacta in zip(valores, exactas))


def _series_dibujables(series: list[dict], dimensiones: tuple) -> bool:
    return all(_coordenadas_dibujables(serie, dimension) for serie, dimension in zip(series, dimensiones))


def _componente_dibujable(valor, exacta: str) -> bool:
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor) and (valor != 0 or exacta == "0"))


def _rango_comun(series: list[dict]) -> list[float] | None:
    magnitud = max(abs(valor) for serie in series for valor in serie["aproximado"])
    limite = magnitud * 1.25 if magnitud else 1.0
    if not math.isfinite(limite) or not math.isfinite(limite * 2):
        return None
    return [-limite, limite]


def _construir_escena(series: list[dict], rango: list, tipo_objeto: str, tema: str) -> dict:
    dimension = len(series[0]["aproximado"])
    figura = graficos.Figure()
    for serie in series:
        _agregar_traza(figura, serie, tipo_objeto)
    fuente = COLORES_TEXTO_GRAFICOS.get(tema, COLORES_TEXTO_GRAFICOS["papel"])
    disposicion = disposicion_2d if dimension == 2 else disposicion_3d
    disposicion(figura, rango_ejes=rango, color_fuente=fuente, revision="aplicacion")
    _identificar_ejes(figura, dimension)
    figura.update_layout(
        autosize=True, showlegend=True, margin=dict(l=30, r=15, t=15, b=35),
        legend=dict(orientation="h", x=0, xanchor="left", y=-0.2, yanchor="top",
                    itemclick=False, itemdoubleclick=False),
    )
    aplicar_colores_figura(figura, tema)
    espacio = "Espacio compartido" if len(series) == 2 else ("Dominio" if series[0]["indice"] == 0 else "Codominio")
    return {"titulo": f"{espacio}: R^{dimension}", "figura": figura}


def _agregar_traza(figura, serie: dict, tipo_objeto: str) -> None:
    valores = serie["aproximado"]
    indice, dimension = serie["indice"], len(valores)
    vector = tipo_objeto == "vector"
    color = PALETA_GRAFICOS[indice]
    simbolo = "circle-open" if indice == 0 else "diamond"
    coordenadas = {eje: [0, valor] if vector else [valor] for eje, valor in zip(("x", "y", "z"), valores)}
    etiqueta = escape("(" + ", ".join(serie["exacta"]) + ")")
    constructor = graficos.Scatter if dimension == 2 else graficos.Scatter3d
    figura.add_trace(constructor(
        **coordenadas, name=("Original", "Transformado")[indice], mode="lines+markers" if vector else "markers",
        line=dict(color=color, width=3, dash="solid" if indice == 0 else "dash"),
        marker=dict(color=color, size=[0, 14 - indice * 5] if vector else 14 - indice * 5, symbol=simbolo),
        customdata=["Origen", etiqueta] if vector else [etiqueta],
        hovertemplate=escape(serie["nombre"]) + ": %{customdata}<extra></extra>",
    ))


def _identificar_ejes(figura, dimension: int) -> None:
    if dimension == 2:
        figura.update_xaxes(title_text="x₁")
        figura.update_yaxes(title_text="x₂")
    else:
        figura.update_layout(scene=dict(xaxis_title="x₁", yaxis_title="x₂", zaxis_title="x₃"))
