"""Pruebas de serialización y límites de las figuras geométricas."""
import pytest

plotly = pytest.importorskip("plotly")


def test_construir_rectas_en_dos_dimensiones():
    """Las rectas bidimensionales generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    result = {
        "n": 2,
        "equations": [
            {"index": 0, "kind": "line", "coeffs": [1.0, 1.0], "coeffs_exact": ["1", "1"], "b": 3.0, "b_exact": "3"},
            {"index": 1, "kind": "line", "coeffs": [1.0, -1.0], "coeffs_exact": ["1", "-1"], "b": 1.0, "b_exact": "1"},
        ],
        "set": {"kind": "POINT", "dimension": 0, "point": [2.0, 1.0], "point_exact": ["2", "1"]},
        "range": [-5.0, 5.0],
    }
    fig = construir_figura_rectas_planos(result)
    fig.to_json()


def test_construir_planos_en_tres_dimensiones():
    """Un plano tridimensional genera JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    result = {
        "n": 3,
        "equations": [
            {"index": 0, "kind": "plane", "coeffs": [1.0, 0.0, 0.0], "coeffs_exact": ["1", "0", "0"], "b": 1.0, "b_exact": "1"},
        ],
        "set": None,
        "range": [-5.0, 5.0],
    }
    fig = construir_figura_rectas_planos(result)
    fig.to_json()


def test_construir_figura_vectores():
    """Los vectores y su cuadro inicial generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_vectores
    result = {
        "n": 2,
        "static": {"u": [1.0, 0.0], "v": [0.0, 1.0], "u_plus_v": [1.0, 1.0]},
        "frames": [{"k": 0.0, "k_exact": "0", "ku": [0.0, 0.0], "ku_plus_v": [0.0, 1.0]}],
        "range": [-5.0, 5.0],
    }
    fig = construir_figura_vectores(result)
    fig.to_json()


def test_construir_figura_combinacion():
    """La combinación y su cadena generan JSON de Plotly válido."""
    from src.frontend.vistas.geometria._escenas import construir_figura_combinacion
    result = {
        "n": 2,
        "b": {"float": [3.0, 3.0], "exact": ["3", "3"]},
        "vectors": [{"float": [1.0, 0.0], "exact": ["1", "0"]}, {"float": [0.0, 1.0], "exact": ["0", "1"]}],
        "chain": [
            {"float": [3.0, 0.0], "exact": ["3", "0"], "label": "c_1·v_1"},
            {"float": [3.0, 3.0], "exact": ["3", "3"], "label": "+ c_2·v_2"},
        ],
        "b_outside_span": False,
        "range": [-5.0, 5.0],
    }
    fig = construir_figura_combinacion(result)
    fig.to_json()


def test_figuras_conservan_rangos_fijos():
    """Los ejes mantienen el intervalo indicado por el controlador."""
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos
    result = {
        "n": 2,
        "equations": [
            {"index": 0, "kind": "line", "coeffs": [1.0, 0.0], "coeffs_exact": ["1", "0"], "b": 10.0, "b_exact": "10"},
        ],
        "set": None,
        "range": [-20.0, 20.0],
    }
    fig = construir_figura_rectas_planos(result)
    layout = fig.layout
    assert list(layout.xaxis.range) == [-20.0, 20.0]
    assert list(layout.yaxis.range) == [-20.0, 20.0]


def test_figuras_no_dependen_de_cuadros_plotly():
    """Las figuras no dependen de la propiedad frames de Plotly."""
    from src.frontend.vistas.geometria._escenas import construir_figura_vectores
    result = {
        "n": 2,
        "static": {"u": [1.0, 0.0], "v": [0.0, 1.0], "u_plus_v": [1.0, 1.0]},
        "frames": [],
        "range": [-5.0, 5.0],
    }
    fig = construir_figura_vectores(result)
    assert not fig.frames
