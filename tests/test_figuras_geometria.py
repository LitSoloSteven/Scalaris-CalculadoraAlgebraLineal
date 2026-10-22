"""Pruebas de serialización y límites de las figuras geométricas."""
import pytest

plotly = pytest.importorskip("plotly")


def test_construir_rectas_en_dos_dimensiones():
    """Las rectas bidimensionales generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    resultado = {
        "numero_variables": 2,
        "ecuaciones": [
            {"indice": 0, "tipo": "recta", "coeficientes": [1.0, 1.0], "coeficientes_exactos": ["1", "1"], "objetivo": 3.0, "objetivo_exacto": "3"},
            {"indice": 1, "tipo": "recta", "coeficientes": [1.0, -1.0], "coeficientes_exactos": ["1", "-1"], "objetivo": 1.0, "objetivo_exacto": "1"},
        ],
        "conjunto_solucion": {"tipo": "PUNTO", "dimension": 0, "punto": [2.0, 1.0], "punto_exacto": ["2", "1"]},
        "rango": [-5.0, 5.0],
    }
    figura = construir_figura_rectas_planos(resultado)
    figura.to_json()


def test_construir_planos_en_tres_dimensiones():
    """Un plano tridimensional genera JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    resultado = {
        "numero_variables": 3,
        "ecuaciones": [
            {"indice": 0, "tipo": "plano", "coeficientes": [1.0, 0.0, 0.0], "coeficientes_exactos": ["1", "0", "0"], "objetivo": 1.0, "objetivo_exacto": "1"},
        ],
        "conjunto_solucion": None,
        "rango": [-5.0, 5.0],
    }
    figura = construir_figura_rectas_planos(resultado)
    figura.to_json()


def test_construir_figura_vectores():
    """Los vectores y su cuadro inicial generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_vectores
    resultado = {
        "numero_variables": 2,
        "estatica": {"vector_u": [1.0, 0.0], "vector_v": [0.0, 1.0], "u_mas_v": [1.0, 1.0]},
        "cuadros": [{"escalar": 0.0, "escalar_exacto": "0", "escalar_por_u": [0.0, 0.0], "escalar_por_u_mas_v": [0.0, 1.0]}],
        "rango": [-5.0, 5.0],
    }
    figura = construir_figura_vectores(resultado)
    figura.to_json()


def test_construir_figura_combinacion():
    """La combinación y su cadena generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_combinacion
    resultado = {
        "numero_variables": 2,
        "objetivo": {"aproximado": [3.0, 3.0], "exacta": ["3", "3"]},
        "vectores": [{"aproximado": [1.0, 0.0], "exacta": ["1", "0"]}, {"aproximado": [0.0, 1.0], "exacta": ["0", "1"]}],
        "cadena": [
            {"aproximado": [3.0, 0.0], "exacta": ["3", "0"], "etiqueta": "c_1·v_1"},
            {"aproximado": [3.0, 3.0], "exacta": ["3", "3"], "etiqueta": "+ c_2·v_2"},
        ],
        "objetivo_fuera_del_espacio_generado": False,
        "rango": [-5.0, 5.0],
    }
    figura = construir_figura_combinacion(resultado)
    figura.to_json()


def test_figuras_conservan_rangos_fijos():
    """Los ejes mantienen el intervalo indicado por el controlador."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    resultado = {
        "numero_variables": 2,
        "ecuaciones": [
            {"indice": 0, "tipo": "recta", "coeficientes": [1.0, 0.0], "coeficientes_exactos": ["1", "0"], "objetivo": 10.0, "objetivo_exacto": "10"},
        ],
        "conjunto_solucion": None,
        "rango": [-20.0, 20.0],
    }
    figura = construir_figura_rectas_planos(resultado)
    disposicion = figura.layout
    assert list(disposicion.xaxis.range) == [-20.0, 20.0]
    assert list(disposicion.yaxis.range) == [-20.0, 20.0]


def test_figuras_no_dependen_de_cuadros_plotly():
    """Las figuras no dependen de la propiedad frames de Plotly."""
    from src.frontend.vistas.geometria._escenas import construir_figura_vectores
    resultado = {
        "numero_variables": 2,
        "estatica": {"vector_u": [1.0, 0.0], "vector_v": [0.0, 1.0], "u_mas_v": [1.0, 1.0]},
        "cuadros": [],
        "rango": [-5.0, 5.0],
    }
    figura = construir_figura_vectores(resultado)
    assert not figura.frames
