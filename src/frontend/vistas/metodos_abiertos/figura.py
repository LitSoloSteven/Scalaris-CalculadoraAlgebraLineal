"""Composición de la curva previa con puntos y rectas del paso seleccionado."""
import math

import plotly.graph_objects as go

from src.frontend.componentes.colores_figuras import aplicar_colores_figura
from src.frontend.componentes.figura_funcion_real import crear_figura_previa
from src.frontend.tema import COLOR_SOLUCION, PALETA_GRAFICOS
from .coordenadas import numero_finito
from .figura_base import crear_figura_vacia
from .puntos_iniciales import agregar_puntos_iniciales


def crear_figura_metodos_abiertos(
    muestra: dict | None, resultado: dict | None, paso=None, *, mostrar_raiz: bool = True,
) -> go.Figure:
    """Dibuja puntos iniciales y la construcción correspondiente al paso activo."""
    respuesta = muestra if muestra and muestra.get("estado") == "EXITO" else None
    figura = crear_figura_previa(respuesta) if respuesta else crear_figura_vacia()
    if resultado:
        _dibujar_resultado(figura, resultado, paso, mostrar_raiz)
        _ajustar_ventana(figura, resultado, paso)
    aplicar_colores_figura(figura, "papel")
    return figura


def _dibujar_resultado(figura, resultado: dict, paso, mostrar_raiz: bool) -> None:
    iteraciones = resultado.get("iteraciones", ())
    if isinstance(paso, dict) and iteraciones:
        _dibujar_paso(figura, iteraciones, paso, resultado, mostrar_raiz)
    else:
        agregar_puntos_iniciales(figura, resultado)
    raiz = resultado.get("raiz")
    if mostrar_raiz and raiz is not None:
        _agregar_raiz(figura, raiz)


def _dibujar_paso(figura, iteraciones, paso, resultado, mostrar_raiz) -> None:
    _agregar_aproximaciones(figura, iteraciones, paso)
    _agregar_recta(figura, paso, resultado["metodo"])
    _agregar_puntos(figura, paso, resultado["metodo"])
    if not mostrar_raiz or not _es_aproximacion_final(paso, resultado):
        _agregar_siguiente_aproximacion(figura, paso, resultado["metodo"])


def _agregar_raiz(figura, raiz) -> None:
    figura.add_trace(go.Scatter(
        x=[raiz], y=[0], mode="markers", name="Raíz aproximada",
        marker=dict(size=11, color=COLOR_SOLUCION),
    ))


def _agregar_puntos(figura, fila: dict, metodo: str) -> None:
    """Marca y etiqueta las evaluaciones actuales, que avanzan en cada iteración."""
    indice = fila.get("i", 1)
    if metodo == "secante":
        datos = [(fila.get("x_anterior"), fila.get("f_x_anterior"), indice - 1),
                 (fila.get("x_n"), fila.get("f_x_n"), indice)]
    else:
        datos = [(fila.get("x_n"), fila.get("f_x_n"), indice - 1)]
    puntos = [(abscisa, ordenada, _etiqueta_x(indice_x))
              for abscisa, ordenada, indice_x in datos
              if abscisa is not None and ordenada is not None]
    if puntos:
        _agregar_traza_puntos(figura, puntos, metodo, indice)


def _agregar_traza_puntos(figura, puntos, metodo: str, indice: int) -> None:
    posicion = ["top left", "top right"] if metodo == "secante" else "top center"
    figura.add_trace(go.Scatter(
        x=[abscisa for abscisa, _, _ in puntos],
        y=[ordenada for _, ordenada, _ in puntos],
        text=[etiqueta for _, _, etiqueta in puntos], textposition=posicion,
        mode="markers+text", name=f"Puntos evaluados · iteración {indice}",
        marker=dict(size=10, color=PALETA_GRAFICOS[1]),
        hovertemplate="%{text} = %{x:.6g}<br>f(%{text}) = %{y:.6g}<extra></extra>",
    ))


def _agregar_aproximaciones(figura, iteraciones: tuple, paso: dict) -> None:
    """Muestra sin etiquetas las aproximaciones previas al paso activo."""
    limite = paso.get("i")
    filas = [fila for fila in iteraciones
             if fila.get("i") is not None and limite is not None and fila["i"] < limite
             and fila.get("x_siguiente") is not None]
    if filas:
        _agregar_traza_aproximaciones(figura, filas)


def _agregar_traza_aproximaciones(figura, filas) -> None:
    figura.add_trace(go.Scatter(
        x=[fila["x_siguiente"] for fila in filas], y=[0] * len(filas),
        customdata=[fila["i"] for fila in filas], mode="lines+markers",
        name="Aproximaciones anteriores",
        line=dict(color=PALETA_GRAFICOS[2], dash="dot"),
        marker=dict(size=7, color=PALETA_GRAFICOS[2]), opacity=0.45,
        hovertemplate="Iteración %{customdata}<br>x siguiente = %{x:.6g}<extra></extra>",
    ))


def _agregar_siguiente_aproximacion(figura, fila: dict, metodo: str) -> None:
    """Resalta el nuevo punto sobre el eje x sin repetir etiquetas de iteración."""
    siguiente = fila.get("x_siguiente")
    if siguiente is None:
        return
    indice = fila.get("i", 1) + (1 if metodo == "secante" else 0)
    etiqueta = _etiqueta_x(indice)
    figura.add_trace(go.Scatter(
        x=[siguiente], y=[0], text=[etiqueta], textposition="bottom center",
        mode="markers+text", name="Siguiente aproximación",
        marker=dict(size=10, color=PALETA_GRAFICOS[2], symbol="diamond"),
        hovertemplate="%{text} = %{x:.6g}<extra></extra>",
    ))


def _es_aproximacion_final(fila: dict, resultado: dict) -> bool:
    """Evita dibujar dos etiquetas en el mismo lugar cuando la iteración converge."""
    siguiente, raiz = fila.get("x_siguiente"), resultado.get("raiz")
    if siguiente is None or raiz is None:
        return False
    return math.isclose(float(siguiente), float(raiz), rel_tol=1e-12, abs_tol=1e-12)


def _etiqueta_x(indice: int) -> str:
    """Forma una etiqueta xₙ breve para que no se monten números de iteración."""
    digitos = str(indice).translate(str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋"))
    return f"x{digitos}"


def _ajustar_ventana(figura, resultado: dict | None, paso) -> None:
    """Encuadra la función alrededor de las aproximaciones y la raíz objetivo."""
    if not resultado:
        return
    rango_x = _rango_abscisas(resultado, paso)
    if rango_x is None:
        return
    rango_y = _rango_ordenadas(figura, rango_x)
    indice = paso.get("i", "inicio") if isinstance(paso, dict) else "inicio"
    revision = f"metodos-abiertos:{resultado.get('metodo')}:{indice}:{rango_x[0]:.12g}:{rango_x[1]:.12g}"
    figura.update_layout(uirevision=revision)
    figura.update_xaxes(range=list(rango_x), autorange=False)
    figura.update_yaxes(range=list(rango_y), autorange=False)


def _rango_abscisas(resultado: dict, paso) -> tuple[float, float] | None:
    puntos = _abscisas_relevantes(resultado, paso)
    raiz = numero_finito(resultado.get("raiz"))
    if raiz is not None:
        puntos.append(raiz)
    puntos = [abscisa for abscisa in puntos if abscisa is not None]
    if not puntos:
        return None
    minimo, maximo = min(puntos), max(puntos)
    escala = max(abs(minimo), abs(maximo))
    margen = max((maximo - minimo) * 0.3, min(0.5, escala * 0.04), 0.05)
    return minimo - margen, maximo + margen


def _abscisas_relevantes(resultado: dict, paso) -> list[float]:
    metodo = resultado.get("metodo")
    if isinstance(paso, dict):
        campos = ["x_n", "x_siguiente"] + (["x_anterior"] if metodo == "secante" else [])
        return [numero_finito(paso.get(campo)) for campo in campos]
    iteraciones = resultado.get("iteraciones", ())
    if iteraciones:
        primera = iteraciones[0]
        campos = ["x_n", "x_anterior"] if metodo == "secante" else ["x_n"]
        return [numero_finito(primera.get(campo)) for campo in campos]
    entrada = resultado.get("entrada") or {}
    campos = ("x0", "x1") if metodo == "secante" else ("x0",)
    return [numero_finito(entrada.get(campo)) for campo in campos]


def _rango_ordenadas(figura, rango_x: tuple[float, float]) -> tuple[float, float]:
    valores = [0.0]
    for traza in figura.data:
        abscisas = list(traza.x) if traza.x is not None else []
        ordenadas = list(traza.y) if traza.y is not None else []
        valores.extend(_ordenadas_en_rango(abscisas, ordenadas, rango_x))
    minimo, maximo = min(valores), max(valores)
    escala = max(abs(minimo), abs(maximo))
    margen = max((maximo - minimo) * 0.12, escala * 0.04, 0.1)
    return minimo - margen, maximo + margen


def _ordenadas_en_rango(abscisas, ordenadas, rango_x) -> list[float]:
    valores = []
    for abscisa, ordenada in zip(abscisas, ordenadas):
        numero_x, numero_y = numero_finito(abscisa), numero_finito(ordenada)
        if numero_x is not None and numero_y is not None and rango_x[0] <= numero_x <= rango_x[1]:
            valores.append(numero_y)
    return valores


def _agregar_recta(figura, fila: dict, metodo: str) -> None:
    """Traza la tangente de Newton o la recta secante correspondiente a la fila."""
    datos = _datos_recta(fila, metodo)
    if datos is None:
        return
    centro, ordenada, pendiente, etiqueta = datos
    abscisas = [centro]
    if fila.get("x_siguiente") is not None:
        abscisas.append(fila["x_siguiente"])
    if metodo == "secante" and fila.get("x_anterior") is not None:
        abscisas.append(fila["x_anterior"])
    extremos = _extremos_recta(abscisas)
    ordenadas = [ordenada + pendiente * (abscisa - centro) for abscisa in extremos]
    figura.add_trace(go.Scatter(
        x=list(extremos), y=ordenadas, mode="lines", name=etiqueta,
        line=dict(color=PALETA_GRAFICOS[0], dash="dash"),
    ))


def _extremos_recta(abscisas) -> tuple[float, float]:
    minimo, maximo = min(abscisas), max(abscisas)
    margen = max((maximo - minimo) * 0.1, 0.25)
    return minimo - margen, maximo + margen


def _datos_recta(fila: dict, metodo: str) -> tuple | None:
    """Extrae punto y pendiente sin repetir evaluaciones del motor numérico."""
    if metodo == "newton" and fila.get("derivada") is not None:
        return fila["x_n"], fila["f_x_n"], fila["derivada"], "Tangente de Newton"
    if metodo == "secante" and fila.get("x_anterior") is not None:
        diferencia = fila["x_n"] - fila["x_anterior"]
        if diferencia != 0:
            pendiente = (fila["f_x_n"] - fila["f_x_anterior"]) / diferencia
            return fila["x_n"], fila["f_x_n"], pendiente, "Secante"
    return None
