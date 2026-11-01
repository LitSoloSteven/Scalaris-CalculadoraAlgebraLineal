"""Traza de apoyo que identifica una componente sin interpolar la transformación."""
from src.frontend.tema import PALETA_GRAFICOS


def anexar_proyeccion(opciones: dict) -> None:
    """Añade una traza vacía solo a las escenas que contienen el resultado transformado."""
    transformada = next((traza for traza in opciones["data"] if traza["name"] == "Transformado"), None)
    if transformada is None:
        return
    dimension = 3 if transformada["type"] == "scatter3d" else 2
    opciones["data"].append({
        "type": transformada["type"], "mode": "markers", "name": "Componente activa",
        **{eje: [] for eje in ("x", "y", "z")[:dimension]},
        "marker": {"color": PALETA_GRAFICOS[1], "size": 12, "symbol": "cross"},
        "showlegend": False, "visible": False,
        "hovertemplate": "%{customdata}<extra>Proyección de componente</extra>",
        "meta": {"scalaris_colores": {"marker.color": "serie:1"},
                 "scalaris_proyeccion": [transformada[eje][-1] for eje in ("x", "y", "z")[:dimension]]},
    })
