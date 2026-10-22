"""Contratos de paleta por tema para todas las familias de figuras."""
import pytest
from src.frontend.tema import PALETAS_POR_TEMA, COLORES_SOLUCION_POR_TEMA, COLORES_TEXTO_GRAFICOS
from src.frontend.vistas.geometria._escenas import (
    construir_figura_rectas_planos, construir_figura_vectores, construir_figura_combinacion,
)


@pytest.mark.parametrize("tema", PALETAS_POR_TEMA)
@pytest.mark.parametrize("dimension", [2, 3])
def test_series_marcadores_superficies_y_solucion(tema, dimension):
    """Rectas y planos exportan roles estables y los colores del tema solicitado."""
    resultado = {
        "numero_variables": dimension,
        "ecuaciones": [{"indice": 2, "tipo": "recta", "coeficientes": [1] * dimension, "objetivo": 1}],
        "conjunto_solucion": {"tipo": "PUNTO", "punto": [1] * dimension},
    }
    figura = construir_figura_rectas_planos(resultado, tema=tema)
    serie, punto = figura.data
    if dimension == 2:
        assert serie.line.color == PALETAS_POR_TEMA[tema][2]
    else:
        assert serie.colorscale[0][1] == PALETAS_POR_TEMA[tema][2]
    assert punto.marker.color == COLORES_TEXTO_GRAFICOS[tema]
    assert punto.marker.line.color == COLORES_TEXTO_GRAFICOS[tema]
    assert figura.layout.xaxis.color == COLORES_TEXTO_GRAFICOS[tema]
    assert figura.layout.scene.zaxis.color == COLORES_TEXTO_GRAFICOS[tema]
    assert serie.meta["scalaris_colores"]


@pytest.mark.parametrize("tema", PALETAS_POR_TEMA)
def test_solucion_lineal_conserva_rol_distinto_de_serie(tema):
    """El color compartido por dos roles en Marea no pierde su identidad."""
    resultado = {"numero_variables": 2, "conjunto_solucion": {
        "tipo": "RECTA", "segmento": [[0, 0], [1, 1]],
    }}
    figura = construir_figura_rectas_planos(resultado, tema=tema)
    assert figura.data[0].line.color == COLORES_SOLUCION_POR_TEMA[tema]
    assert figura.data[0].meta["scalaris_colores"]["line.color"] == "solucion"


@pytest.mark.parametrize("tema", PALETAS_POR_TEMA)
@pytest.mark.parametrize("dimension", [2, 3])
def test_vectores_y_combinacion_no_dejan_marcadores_por_defecto(tema, dimension):
    """Las puntas y las cadenas usan colores explícitos en ambas dimensiones."""
    vector = [1] * dimension
    resultado = {"numero_variables": dimension, "estatica": {
        "vector_u": vector, "vector_v": vector, "u_mas_v": vector,
    }, "vectores": [{"aproximado": vector}], "objetivo": {"aproximado": vector}}
    for constructor in (construir_figura_vectores, construir_figura_combinacion):
        figura = constructor(resultado, tema=tema)
        assert figura.data[0].line.color == PALETAS_POR_TEMA[tema][0]
        assert figura.data[0].marker.color == PALETAS_POR_TEMA[tema][0]
        assert all(traza.meta["scalaris_colores"] for traza in figura.data)


def test_tema_desconocido_y_figura_vacia():
    """Un tema desconocido conserva el fallback y los datos vacíos no fallan."""
    figura = construir_figura_vectores({}, tema="desconocido")
    assert not figura.data
    assert figura.layout.font.color == COLORES_TEXTO_GRAFICOS["papel"]
