"""Puntos capturados y aproximaciones iniciales de Newton y secante."""
import math

import plotly.graph_objects as go

from src.frontend.tema import PALETA_GRAFICOS
from .coordenadas import numero_finito


def agregar_puntos_iniciales(figura, resultado: dict) -> None:
    """Marca los puntos de entrada incluso cuando el método no registra iteraciones."""
    iteraciones = resultado.get("iteraciones", ())
    datos = (_datos_primera_iteracion(iteraciones[0], resultado.get("metodo"))
             if iteraciones else _datos_capturados(figura, resultado))
    puntos = [(abscisa, ordenada, etiqueta) for abscisa, ordenada, etiqueta in datos
              if abscisa is not None and ordenada is not None]
    if puntos:
        _agregar_traza_inicial(figura, puntos)


def _agregar_traza_inicial(figura, puntos) -> None:
    figura.add_trace(go.Scatter(
        x=[abscisa for abscisa, _, _ in puntos],
        y=[ordenada for _, ordenada, _ in puntos],
        text=[etiqueta for _, _, etiqueta in puntos], textposition="top center",
        mode="markers+text", name="Puntos iniciales",
        marker=dict(size=11, color=PALETA_GRAFICOS[1], symbol="diamond"),
        hovertemplate="%{text} = %{x}<br>f(%{text}) = %{y}<extra></extra>",
    ))


def _datos_primera_iteracion(primera: dict, metodo: str) -> list[tuple]:
    if metodo == "secante":
        return [(primera.get("x_anterior"), primera.get("f_x_anterior"), "x₀"),
                (primera.get("x_n"), primera.get("f_x_n"), "x₁")]
    return [(primera.get("x_n"), primera.get("f_x_n"), "x₀")]


def _datos_capturados(figura, resultado: dict) -> list[tuple]:
    entrada = resultado.get("entrada") or {}
    contexto = resultado.get("contexto_fallo") or {}
    metodo = resultado.get("metodo")
    campos = (("x0", "f0", "x₀"), ("x1", "f1", "x₁")) if metodo == "secante" else (
        ("x0", "f_x", "x₀"),)
    datos = []
    for campo_x, campo_y, etiqueta in campos:
        abscisa = _obtener_abscisa(entrada, contexto, campo_x, metodo)
        ordenada = _obtener_ordenada(figura, contexto, campo_y, abscisa, resultado.get("raiz"))
        datos.append((abscisa, ordenada, etiqueta))
    return datos


def _obtener_abscisa(entrada, contexto, campo: str, metodo: str):
    abscisa = contexto.get(campo)
    if abscisa is None and metodo == "newton" and campo == "x0":
        abscisa = contexto.get("x")
    return numero_finito(entrada.get(campo) if abscisa is None else abscisa)


def _obtener_ordenada(figura, contexto, campo: str, abscisa, raiz):
    ordenada = numero_finito(contexto.get(campo))
    if ordenada is not None:
        return ordenada
    if abscisa is None:
        return None
    interpolada = _interpolar_ordenada(figura, abscisa)
    if interpolada is not None:
        return interpolada
    return 0.0 if raiz is not None and math.isclose(
        abscisa, float(raiz), rel_tol=1e-12, abs_tol=1e-12) else None


def _interpolar_ordenada(figura, abscisa: float) -> float | None:
    for traza in figura.data:
        if traza.x is None or traza.y is None or len(traza.x) < 2:
            continue
        ordenada = _interpolar_en_traza(traza.x, traza.y, abscisa)
        if ordenada is not None:
            return ordenada
    return None


def _interpolar_en_traza(abscisas, ordenadas, objetivo: float) -> float | None:
    for indice in range(1, min(len(abscisas), len(ordenadas))):
        inicio_x, fin_x = numero_finito(abscisas[indice - 1]), numero_finito(abscisas[indice])
        inicio_y, fin_y = numero_finito(ordenadas[indice - 1]), numero_finito(ordenadas[indice])
        if None in (inicio_x, fin_x, inicio_y, fin_y) or inicio_x == fin_x:
            continue
        if min(inicio_x, fin_x) <= objetivo <= max(inicio_x, fin_x):
            proporcion = (objetivo - inicio_x) / (fin_x - inicio_x)
            return inicio_y + proporcion * (fin_y - inicio_y)
    return None
