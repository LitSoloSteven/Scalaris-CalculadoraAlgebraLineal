"""Asigna roles cromáticos a las trazas para conservarlos al cambiar de tema."""
from src.frontend.tema import (
    PALETA_GRAFICOS, COLOR_SOLUCION, COLOR_MARCADOR_CLARO, COLOR_MARCADOR_BORDE,
    COLORES_TEXTO_GRAFICOS, COLORES_CUADRICULA_GRAFICOS,
    obtener_paleta_tema, obtener_color_solucion,
)


def _rol_color(color: str) -> str:
    if color in PALETA_GRAFICOS:
        return f"serie:{PALETA_GRAFICOS.index(color)}"
    if color == COLOR_SOLUCION:
        return "solucion"
    if color in (COLOR_MARCADOR_CLARO, COLOR_MARCADOR_BORDE):
        return "texto"
    raise ValueError(f"Color gráfico sin rol: {color}")


def _color_rol(rol: str, tema: str) -> str:
    if rol.startswith("serie:"):
        return obtener_paleta_tema(tema)[int(rol.split(":")[1])]
    if rol == "solucion":
        return obtener_color_solucion(tema)
    return COLORES_TEXTO_GRAFICOS[tema]


def _colorear_traza(traza, tema: str) -> None:
    roles = {}
    datos = traza.to_plotly_json()
    for ruta in ("line.color", "marker.color", "marker.line.color", "colorscale"):
        valor = datos
        for clave in ruta.split("."):
            valor = valor.get(clave, {}) if isinstance(valor, dict) else {}
        if not valor:
            continue
        rol = _rol_color(valor[0][1] if ruta == "colorscale" else valor)
        roles[ruta] = rol
        color = _color_rol(rol, tema)
        traza[ruta] = [[0, color], [1, color]] if ruta == "colorscale" else color
    if "line.color" in roles and "marker" in traza and "marker.color" not in roles:
        roles["marker.color"] = roles["line.color"]
        traza.marker.color = traza.line.color
    traza.meta = {"scalaris_colores": roles}


def aplicar_colores_figura(figura, tema: str) -> None:
    """Aplica el tema a la figura Plotly y registra roles; retorna None.
    Los temas desconocidos usan Papel, sin modificar coordenadas ni la revisión de cámara.
    """
    tema = tema if tema in COLORES_TEXTO_GRAFICOS else "papel"
    for traza in figura.data:
        _colorear_traza(traza, tema)
    texto = COLORES_TEXTO_GRAFICOS[tema]
    cuadricula = COLORES_CUADRICULA_GRAFICOS[tema]
    ejes = dict(color=texto, gridcolor=cuadricula, zerolinecolor=texto)
    figura.update_layout(font_color=texto, xaxis=ejes, yaxis=ejes,
                         scene=dict(xaxis=ejes, yaxis=ejes, zaxis=ejes))
