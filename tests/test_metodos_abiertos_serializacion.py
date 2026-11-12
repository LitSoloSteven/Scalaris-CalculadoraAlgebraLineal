"""Serialización JSON de resultados y filas de los métodos abiertos."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.metodos_abiertos import newton, secante


def _serializar(resultado):
    datos = asdict(resultado)
    return datos, json.dumps(datos, allow_nan=False)


def test_resultados_de_newton_serializan_en_todos_los_estados():
    """Éxitos y fallos de Newton producen JSON estricto, sin NaN ni infinitos."""
    resultados = [
        newton({"metodo": "newton", "expresion": "x^3 - x - 2", "x0": 1.5}),
        newton({"metodo": "newton", "expresion": "x^2 + 1", "x0": 0}),
        newton({"metodo": "newton", "expresion": "x + 2e12", "x0": 0}),
        newton({"metodo": "newton", "expresion": "ln(x)", "x0": -1}),
        newton({"metodo": "newton", "expresion": "x^x", "x0": 1}),
        newton({"metodo": "newton", "expresion": "x - 1", "x0": 0, "tolerancia": 0}),
    ]
    for resultado in resultados:
        _, texto = _serializar(resultado)
        assert "NaN" not in texto and "Infinity" not in texto


def test_resultados_de_secante_serializan_en_todos_los_estados():
    """Éxitos y fallos de la secante también producen JSON estricto."""
    resultados = [
        secante({"metodo": "secante", "expresion": "x^3 - x - 2", "x0": 1, "x1": 2}),
        secante({"metodo": "secante", "expresion": "1", "x0": 1, "x1": 2}),
        secante({"metodo": "secante", "expresion": "x - 2", "x0": 2, "x1": 3}),
        secante({"metodo": "secante", "expresion": "ln(x)", "x0": -1, "x1": 2}),
        secante({"metodo": "secante", "expresion": "1/x", "x0": 1, "x1": 2, "tolerancia": 1e-15}),
        secante(
            {
                "metodo": "secante",
                "expresion": "x^2 - 2",
                "x0": 1,
                "x1": 2,
                "tolerancia": 1e-15,
                "limite_iteraciones": 1,
            }
        ),
    ]
    for resultado in resultados:
        _, texto = _serializar(resultado)
        assert "NaN" not in texto and "Infinity" not in texto


def test_campos_opcionales_se_serializan_como_none():
    """Los campos que no aplican a un método no se omiten del JSON."""
    datos, _ = _serializar(newton({"metodo": "newton", "expresion": "x^3 - x - 2", "x0": 1.5}))
    fila = datos["iteraciones"][0]
    assert fila["x_anterior"] is None
    assert fila["f_x_anterior"] is None


def test_secante_serializa_derivada_nula():
    """La secante conserva derivada=None en cada fila."""
    datos, _ = _serializar(secante({"metodo": "secante", "expresion": "x^3 - x - 2", "x0": 1, "x1": 2}))
    assert datos["iteraciones"][0]["derivada"] is None


def test_total_de_iteraciones_coincide_con_las_filas():
    """El contador total siempre refleja la tupla serializada."""
    for resultado in (
        newton({"metodo": "newton", "expresion": "x^3 - x - 2", "x0": 1.5}),
        secante({"metodo": "secante", "expresion": "x^3 - x - 2", "x0": 1, "x1": 2}),
    ):
        datos, _ = _serializar(resultado)
        assert datos["iteraciones_totales"] == len(datos["iteraciones"])


def test_error_de_entrada_tambien_es_serializable():
    """Un resultado de error conserva la entrada y el contexto sin valores especiales."""
    resultado = newton({"metodo": "newton", "expresion": "ln(x)", "x0": -1})
    datos, texto = _serializar(resultado)
    assert datos["contexto_fallo"]["x"] == -1
    assert "NaN" not in texto and "Infinity" not in texto
