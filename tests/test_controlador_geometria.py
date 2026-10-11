"""Pruebas del controlador y algoritmos de geometría analítica."""
import copy
import json
from fractions import Fraction
import pytest

from src.backend.geometria.recorte import (
    calcular_rango_automatico,
    recortar_recta_a_caja,
)
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
    selector_celda_error,
)


def test_rango_automatico_simetrico():
    rango = calcular_rango_automatico([3.0, -2.0])
    assert rango[0] == -rango[1]
    assert rango[1] >= 3.0


def test_rango_automatico_minimo():
    rango = calcular_rango_automatico([0.5])
    assert rango[1] >= 5.0


def test_rango_automatico_escala_125():
    rango = calcular_rango_automatico([7.0])
    assert rango == [-10.0, 10.0]


def test_rango_automatico_sin_finitos():
    rango = calcular_rango_automatico([float("inf"), float("-inf"), float("nan")])
    assert rango == [-5.0, 5.0]


def test_rango_automatico_vacio():
    rango = calcular_rango_automatico([])
    assert rango == [-5.0, 5.0]


def test_rango_automatico_valores_nulos():
    rango = calcular_rango_automatico([None, 3.0, None])
    assert rango[0] == -rango[1]


def test_rango_automatico_tope_grande():
    rango = calcular_rango_automatico([1e15])
    assert rango[1] <= 1e6


def test_recorte_recta_caja_interior():
    resultado = recortar_recta_a_caja([0.0, 0.0], [1.0, 0.0], 5.0)
    assert resultado is not None
    assert abs(resultado[0] - (-5.0)) < 1e-6
    assert abs(resultado[1] - 5.0) < 1e-6


def test_recorte_recta_caja_exterior_cruce():
    resultado = recortar_recta_a_caja([10.0, 0.0], [1.0, 0.0], 5.0)
    assert resultado is not None
    assert abs(resultado[0] - (-15.0)) < 1e-6
    assert abs(resultado[1] - (-5.0)) < 1e-6


def test_recorte_recta_caja_paralela_exterior():
    resultado = recortar_recta_a_caja([0.0, 10.0], [1.0, 0.0], 5.0)
    assert resultado is None


def test_recorte_recta_caja_direccion_cero():
    resultado = recortar_recta_a_caja([0.0, 0.0], [0.0, 0.0], 5.0)
    assert resultado is None


def test_selector_celda_error_matriz_a():
    resultado = selector_celda_error({"kind": "A", "row": 1, "col": 2}, escena="rectas-planos", n_cuadricula=2)
    assert resultado == 'input[data-row="1"][data-col="2"]'


def test_selector_celda_error_vector_b():
    resultado = selector_celda_error({"kind": "b", "row": 1}, escena="rectas-planos", n_cuadricula=2)
    assert resultado == 'input[data-row="1"][data-col="2"]'


def test_selector_celda_error_vector():
    resultado = selector_celda_error({"kind": "vec", "name": "v_1", "index": 0}, escena="vectores", n_cuadricula=2)
    assert resultado == 'input[data-geometria-vector="geometria_vectores_v_1"][data-geometria-indice="0"]'


def test_selector_celda_error_combinacion():
    resultado = selector_celda_error({"kind": "vec", "name": "b", "index": 1}, escena="combinacion", n_cuadricula=2)
    assert resultado == 'input[data-geometria-vector="geometria_combinacion_b"][data-geometria-indice="1"]'


def test_rectas_planos_payload_malformado():
    resultado = ControladorGeometria.procesar_rectas_planos("not json")
    assert resultado["status"] == "ERROR"


def test_rectas_planos_interseccion_unica_dos_por_dos():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 2
    assert resultado["solution_status"] == "UNIQUE_SOLUTION"
    assert resultado["set"]["kind"] == "POINT"
    assert resultado["set"]["point"] == [2.0, 1.0]
    assert resultado["set"]["point_exact"] == ["2", "1"]
    assert not resultado["pending_param"]
    json.dumps(resultado)


def test_rectas_planos_indicador_paralelismo():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "NO_SOLUTION"
    assert "parallel" in resultado["flags"]


def test_rectas_planos_degenerada_cero_igual_cero():
    payload = json.dumps({
        "matrix_A": [["0", "0"], ["1", "1"]],
        "vector_b": ["0", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    ecuaciones = resultado["equations"]
    assert ecuaciones[0]["kind"] == "trivial"


def test_rectas_planos_degenerada_cero_igual_cinco():
    payload = json.dumps({
        "matrix_A": [["0", "0"], ["1", "1"]],
        "vector_b": ["5", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    ecuaciones = resultado["equations"]
    assert ecuaciones[0]["kind"] == "contradiction"


def test_rectas_planos_dimension_cuatro_invalida():
    payload = json.dumps({
        "matrix_A": [["1", "0", "0", "0"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") == "bad_dimension"


def test_rectas_planos_dimension_diez_invalida():
    fila = ["1"] * 10
    payload = json.dumps({
        "matrix_A": [fila],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") == "bad_dimension"


def test_rectas_planos_fracciones_largas():
    payload = json.dumps({
        "matrix_A": [["1001/1000", "1"], ["1", "-123456789012/987654321"]],
        "vector_b": ["3", "1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    json.dumps(resultado)


def test_rectas_planos_diez_ecuaciones():
    filas = [["1", str(i)] for i in range(10)]
    vector_b = [str(i) for i in range(10)]
    payload = json.dumps({"matrix_A": filas, "vector_b": vector_b})
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["m"] == 10


def test_rectas_planos_celda_erronea():
    payload = json.dumps({
        "matrix_A": [["1", "abc"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "ERROR"
    assert resultado["error_cell"] is not None
    assert resultado["error_cell"]["kind"] == "A"


def test_rectas_planos_serializable():
    payload = json.dumps({
        "matrix_A": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    serializado = json.dumps(resultado)
    assert isinstance(serializado, str)


def test_rectas_planos_sin_mutacion():
    diccionario_carga = {
        "matrix_A": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    }
    carga_str = json.dumps(diccionario_carga)
    original = copy.deepcopy(diccionario_carga)
    ControladorGeometria.procesar_rectas_planos(carga_str)
    assert diccionario_carga == original


def test_rectas_planos_tres_por_tres_solucion_unica():
    payload = json.dumps({
        "matrix_A": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["1", "2", "3"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 3
    assert resultado["solution_status"] == "UNIQUE_SOLUTION"
    assert resultado["set"]["point"] == [1.0, 2.0, 3.0]


def test_rectas_planos_soluciones_infinitas():
    payload = json.dumps({
        "matrix_A": [["1", "1"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(payload)
    assert resultado["status"] == "OK"
    assert resultado["pending_param"] is False
    assert resultado["set"] is not None
    assert resultado["set"]["kind"] == "LINE"
    assert "segment" in resultado["set"] and resultado["set"]["segment"] is not None


def test_vectores_basico_dos_dimensiones():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(payload)
    assert resultado["status"] == "OK"
    assert resultado["n"] == 2
    assert len(resultado["frames"]) == 25


def test_vectores_cuadro_predeterminado_k_uno():
    payload = json.dumps({
        "vectors": [
            {"data": ["2", "3"], "orientation": "column"},
            {"data": ["1", "1"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(payload)
    assert resultado["status"] == "OK"
    cuadro_defecto = resultado["default_frame"]
    cuadro = resultado["frames"][cuadro_defecto]
    u = resultado["u"]["float"]
    v = resultado["v"]["float"]
    assert cuadro["ku"] == u
    assert cuadro["ku_plus_v"] == [u[0] + v[0], u[1] + v[1]]


def test_vectores_rango_cubre_todos_los_cuadros():
    payload = json.dumps({
        "vectors": [
            {"data": ["10", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(payload)
    r = resultado["range"]
    assert r[1] >= 30


def test_vectores_dimension_cuatro_invalida():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "0", "0", "0"], "orientation": "column"},
            {"data": ["0", "1", "0", "0"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(payload)
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") == "bad_dimension"


def test_combinacion_cadena_unica():
    payload = json.dumps({
        "b": {"data": ["3", "3"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "UNIQUE"
    cadena = resultado["chain"]
    assert cadena is not None
    ultimo = cadena[-1]
    b_exacto = resultado["b"]["exact"]
    assert ultimo["exact"] == b_exacto


def test_combinacion_soluciones_infinitas():
    payload = json.dumps({
        "b": {"data": ["0", "0"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["2", "0"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(payload)
    assert resultado["status"] == "OK"
    if resultado["solution_status"] == "INFINITE":
        assert resultado["chain"] is None
        assert resultado["representation"] == "non_unique"


def test_combinacion_sin_solucion():
    payload = json.dumps({
        "b": {"data": ["0", "1"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(payload)
    assert resultado["status"] == "OK"
    assert resultado["solution_status"] == "NO_SOLUTION"
    assert resultado["b_outside_span"]
    assert resultado["chain"] is None


def test_combinacion_dimension_cuatro_invalida():
    payload = json.dumps({
        "b": {"data": ["1", "2", "3", "4"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0", "0", "0"], "orientation": "column"},
        ],
    })
    resultado = ControladorGeometria.procesar_combinacion(payload)
    assert resultado["status"] == "ERROR"
    assert resultado.get("code") == "bad_dimension"
