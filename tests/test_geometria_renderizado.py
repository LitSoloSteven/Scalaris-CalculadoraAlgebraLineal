"""Pruebas de renderizado y conjunto solución en geometría analítica."""
import json
from fractions import Fraction
import pytest

from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)


def test_controlador_recta_dos_dimensiones():
    """Verifica que una ecuación en 2D produzca un segmento acotado en la caja."""
    payload = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 2
    assert resultado["pending_param"] is False

    sol_set = resultado["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1
    assert sol_set["whole_space"] is False

    semi_ancho = resultado["range"][1]
    segmento = sol_set.get("segment")
    assert segmento is not None
    assert len(segmento) == 2
    for punto in segmento:
        assert len(punto) == 2
        for coord in punto:
            assert -semi_ancho - 1e-4 <= coord <= semi_ancho + 1e-4

    assert "param_latex" in sol_set and sol_set["param_latex"].startswith(r"\mathbf{x} = ")
    assert "description" in sol_set and "Las soluciones forman una recta" in sol_set["description"]
    assert "point_latex" in sol_set and sol_set["point_latex"] is not None


def test_controlador_plano_tres_dimensiones():
    """Verifica que una ecuación en 3D genere normal analítica y desplazamiento."""
    payload = json.dumps({
        "matrix_A": [["1", "1", "1"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 3
    assert resultado["pending_param"] is False

    sol_set = resultado["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "PLANE"
    assert sol_set["dimension"] == 2
    assert sol_set["whole_space"] is False

    assert "normal_exact" in sol_set
    assert "offset_exact" in sol_set
    nx = Fraction(sol_set["normal_exact"][0])
    ny = Fraction(sol_set["normal_exact"][1])
    nz = Fraction(sol_set["normal_exact"][2])
    assert nx == ny == nz != 0
    assert Fraction(sol_set["offset_exact"]) / nx == 1

    assert "param_latex" in sol_set and sol_set["param_latex"].startswith(r"\mathbf{x} = ")
    assert "description" in sol_set and "Las soluciones forman un plano" in sol_set["description"]


def test_controlador_interseccion_dos_planos_recta_tres_dimensiones():
    """Dos planos independientes en 3D generan una recta con segmento de 3 coordenadas."""
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 3

    sol_set = resultado["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1

    segmento = sol_set.get("segment")
    assert segmento is not None
    assert len(segmento) == 2
    assert len(segmento[0]) == 3
    assert len(segmento[1]) == 3


def test_controlador_todo_el_espacio():
    """Verifica que ecuaciones nulas marquen whole_space como True."""
    payload2 = json.dumps({"matrix_A": [["0", "0"]], "vector_b": ["0"]})
    res2 = ControladorGeometria.procesar_rectas_planos(payload2)
    assert res2["status"] == "OK"
    assert res2["set"]["whole_space"] is True

    payload3 = json.dumps({"matrix_A": [["0", "0", "0"]], "vector_b": ["0"]})
    res3 = ControladorGeometria.procesar_rectas_planos(payload3)
    assert res3["status"] == "OK"
    assert res3["set"]["whole_space"] is True


def test_controlador_fracciones_analiticas_largas():
    """Verifica resolución analítica exacta con denominadores extensos."""
    payload = json.dumps({
        "matrix_A": [["1001/1000", "-123456789012/987654321"]],
        "vector_b": ["1/2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["pending_param"] is False

    sol_set = resultado["set"]
    assert sol_set is not None

    fila_a = [Fraction("1001/1000"), Fraction("-123456789012/987654321")]
    valor_b = Fraction("1/2")

    p_exacto = [Fraction(x) for x in sol_set["point_exact"]]
    assert sum(a * p for a, p in zip(fila_a, p_exacto)) == valor_b

    for d_lista in sol_set["directions_exact"]:
        d_exacto = [Fraction(x) for x in d_lista]
        assert sum(a * d for a, d in zip(fila_a, d_exacto)) == 0

    assert "param_latex" in sol_set
    assert sol_set["param_latex"].startswith(r"\mathbf{x} = ")


def test_controlador_solucion_unica_punto_latex():
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["-1", "10", "1/2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "UNIQUE_SOLUTION"
    assert resultado["pending_param"] is False

    sol_set = resultado["set"]
    assert sol_set["kind"] == "POINT"
    assert sol_set["point_latex"] is not None
    assert r"\begin{bmatrix}" in sol_set["point_latex"]
    assert "-1" in sol_set["point_latex"]
    assert "10" in sol_set["point_latex"]
    assert r"\frac{1}{2}" in sol_set["point_latex"]


def test_controlador_sin_solucion():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "NO_SOLUTION"
    assert resultado["pending_param"] is False


def test_controlador_rectas_paralelas():
    payload = json.dumps({
        "matrix_A": [["1", "2"], ["2", "4"]],
        "vector_b": ["3", "7"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "NO_SOLUTION"
    assert "parallel" in resultado["flags"]


def test_controlador_simulado_sin_parametros_solucion(monkeypatch):
    resolutor_orig = getattr(ResolutorGauss, "resolver", getattr(ResolutorGauss, "solve", None))

    def resolutor_simulado(self):
        res = resolutor_orig(self)
        if res.get("status") == "INFINITE_SOLUTIONS" or res.get("estado") == "INFINITAS":
            res.pop("solution_param", None)
            res.pop("parametros_solucion", None)
        return res

    monkeypatch.setattr(ResolutorGauss, "resolver", resolutor_simulado)
    if hasattr(ResolutorGauss, "solve"):
        monkeypatch.setattr(ResolutorGauss, "solve", resolutor_simulado)

    payload = json.dumps({"matrix_A": [["1", "1"]], "vector_b": ["1"]})
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "INFINITE_SOLUTIONS"
    assert resultado["pending_param"] is True
    assert resultado["set"] is None


def test_figuras_recta_dos_dimensiones_y_plano_tres_dimensiones():
    pytest.importorskip("plotly")
    from src.frontend.vistas.geometria._escenas import construir_figura_rectas_planos

    payload_2d = json.dumps({"matrix_A": [["1", "1"]], "vector_b": ["2"]})
    res_2d = ControladorGeometria.procesar_rectas_planos(payload_2d)
    fig_2d = construir_figura_rectas_planos(res_2d, tema="papel")
    nombres_2d = [t.name for t in fig_2d.data]
    assert "Conjunto solución (recta)" in nombres_2d
    assert "Ecuación 1" in nombres_2d

    payload_3d = json.dumps({"matrix_A": [["1", "1", "1"]], "vector_b": ["1"]})
    res_3d = ControladorGeometria.procesar_rectas_planos(payload_3d)
    fig_3d = construir_figura_rectas_planos(res_3d, tema="papel")
    nombres_3d = [t.name for t in fig_3d.data]
    assert "Conjunto solución (plano)" in nombres_3d
    assert "Ecuación 1" in nombres_3d

    payload_ws = json.dumps({"matrix_A": [["0", "0"]], "vector_b": ["0"]})
    res_ws = ControladorGeometria.procesar_rectas_planos(payload_ws)
    fig_ws = construir_figura_rectas_planos(res_ws, tema="papel")
    nombres_ws = [t.name for t in fig_ws.data]
    assert "Conjunto solución (recta)" not in nombres_ws
    assert "Conjunto solución (plano)" not in nombres_ws


def test_vista_construir_payload_cuadricula_vacia():
    class CuadriculaSimulada:
        def is_strictly_empty(self):
            return True
        def obtener_datos_matriz(self):
            return [["", ""]], [""]

    class InterfazSimulada:
        def __init__(self):
            self.scene = "rectas-planos"
            self.grid = CuadriculaSimulada()

        def _build_payload(self):
            if self.scene == "rectas-planos":
                if not self.grid or self.grid.is_strictly_empty():
                    return None
                matrix_a, vector_b = self.grid.obtener_datos_matriz()
                if not matrix_a or not matrix_a[0]:
                    return None
                return {"matrix_A": matrix_a, "vector_b": vector_b}
            return None

    ui = InterfazSimulada()
    assert ui._build_payload() is None
