"""Pruebas de robustez y rendimiento ante datos límite y entradas extremas."""
import json
import time
from fractions import Fraction
import pytest

from src.backend.solvers.numeric_systems.conversor_bases import ConversorBases
from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator,
    RomanNumeralError,
)
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.glosa_render import render_glosa_text
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)
from src.frontend.controladores.operaciones_inversas.controlador_operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.controladores.operaciones_vectores.controlador_operaciones_vectores import (
    ControladorOperacionesVectores,
)
from src.frontend.controladores.sistemas_lineales.controlador_gauss import (
    ControladorGauss,
)
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import (
    ControladorGaussJordan,
)


def test_entradas_celdas_extremas_e_invalidas():
    casos = [
        ("1001/1000", True),
        ("-123456789012/987654321", True),
        ("0.0000001", True),
        ("1/0", False),
        ("abc", False),
        ("", False),
    ]

    for val_str, debe_ser_valido in casos:
        t0 = time.perf_counter()
        ok, parseado, err_msg = ValidadorMatriz.parsear_numero_exacto(val_str)
        duracion = time.perf_counter() - t0

        assert duracion < 0.05
        assert ok is debe_ser_valido
        assert isinstance(parseado, Fraction)
        assert "Traceback" not in err_msg
        if not ok:
            assert len(err_msg) > 0


def test_controlador_geometria_los_tres_procesos():
    p_rectas = json.dumps({
        "matrix_A": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
    })
    t0 = time.perf_counter()
    r_rectas = ControladorGeometria.procesar_rectas_planos(p_rectas)
    assert time.perf_counter() - t0 < 1.0
    assert r_rectas.get("status") == "OK"
    assert "Traceback" not in r_rectas.get("message", "")
    json.dumps(r_rectas)

    p_vecs = json.dumps({
        "vectors": [
            {"data": ["1", "2"], "orientation": "column"},
            {"data": ["3", "4"], "orientation": "column"},
        ]
    })
    t0 = time.perf_counter()
    r_vecs = ControladorGeometria.procesar_vectores(p_vecs)
    assert time.perf_counter() - t0 < 1.0
    assert r_vecs.get("status") == "OK"
    assert "Traceback" not in r_vecs.get("message", "")
    json.dumps(r_vecs)

    p_comb = json.dumps({
        "b": {"data": ["5", "6"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    t0 = time.perf_counter()
    r_comb = ControladorGeometria.procesar_combinacion(p_comb)
    assert time.perf_counter() - t0 < 1.0
    assert r_comb.get("status") == "OK"
    assert "Traceback" not in r_comb.get("message", "")
    json.dumps(r_comb)


def test_controlador_inversas_cincuenta_por_cincuenta_identidad():
    n = 50
    mat_ident = [[("1/2" if i == j else "0") for j in range(n)] for i in range(n)]
    payload = json.dumps({"n": n, "data": mat_ident})

    t0 = time.perf_counter()
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert time.perf_counter() - t0 < 30.0
    assert res.get("status") == "SUCCESS"
    assert "Traceback" not in res.get("message", "")
    assert res.get("n") == 50


def test_controlador_inversas_cincuenta_por_cincuenta_singular():
    n = 50
    mat_sing = [[("1" if i == j else "0") for j in range(n)] for i in range(n)]
    mat_sing[1] = list(mat_sing[0])
    payload = json.dumps({"n": n, "data": mat_sing})

    t0 = time.perf_counter()
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert time.perf_counter() - t0 < 0.5
    assert res.get("status") == "SINGULAR"
    assert "Traceback" not in res.get("message", "")
    assert res.get("n") == 50


def test_sistemas_lineales_diez_por_diez_inconsistente():
    mat_10 = [["1" if i == j else "0" for j in range(10)] for i in range(10)]
    mat_10[9] = ["0"] * 10
    b_10 = ["1"] * 9 + ["5"]
    payload = json.dumps({"matrix_A": mat_10, "vector_b": b_10})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 1.0
    assert res_gauss.get("status") == "NO_SOLUTION"

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 1.0
    assert res_gj.get("status") == "NO_SOLUTION"


def test_sistemas_lineales_uno_por_uno():
    payload = json.dumps({"matrix_A": [["2"]], "vector_b": ["6"]})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 0.5
    assert res_gauss.get("status") == "UNIQUE_SOLUTION"
    assert res_gauss.get("solution") == ["3"]

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 0.5
    assert res_gj.get("status") == "UNIQUE_SOLUTION"
    assert res_gj.get("solution") == ["3"]


def test_sistemas_lineales_diez_por_uno():
    mat = [[str(i + 1)] for i in range(10)]
    b = [str((i + 1) * 2) for i in range(10)]
    payload = json.dumps({"matrix_A": mat, "vector_b": b})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 0.5
    assert res_gauss.get("status") == "UNIQUE_SOLUTION"
    assert res_gauss.get("solution") == ["2"]

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(payload))
    assert time.perf_counter() - t0 < 0.5
    assert res_gj.get("status") == "UNIQUE_SOLUTION"
    assert res_gj.get("solution") == ["2"]


def test_combinacion_lineal_vectores_diez_dimensiones():
    b_v = {"data": [str(i + 1) for i in range(10)], "orientation": "column"}
    vectors_9 = [
        {"data": [("1" if i == j else "0") for i in range(10)], "orientation": "column"}
        for j in range(9)
    ]
    payload = json.dumps({"b": b_v, "vectors": vectors_9})

    t0 = time.perf_counter()
    res = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(payload))
    assert time.perf_counter() - t0 < 2.0
    assert res.get("status") in ("INCONSISTENT", "NO_SOLUTION", "UNIQUE", "INFINITE")
    assert "Traceback" not in res.get("message", "")


def test_calculadora_romana_desbordamiento_y_cero():
    t0 = time.perf_counter()
    try:
        RomanCalculator.sumar("MMMCMXCIX", "I")
        err_suma = None
    except (RomanNumeralError, ValueError) as e:
        err_suma = str(e)
    assert time.perf_counter() - t0 < 0.1
    assert err_suma is not None
    assert "Traceback" not in err_suma

    t0 = time.perf_counter()
    try:
        RomanCalculator.restar("V", "V")
        err_resta = None
    except (RomanNumeralError, ValueError) as e:
        err_resta = str(e)
    assert time.perf_counter() - t0 < 0.1
    assert err_resta is not None
    assert "cero" in err_resta.lower()


def test_conversor_bases_enteros_grandes_y_negativos():
    conv = ConversorBases()
    val_grande = str(2 ** 200 - 1)
    t0 = time.perf_counter()
    r_grande = conv.decimal_a_todo(val_grande)
    assert time.perf_counter() - t0 < 0.5
    assert "error" not in r_grande
    assert len(r_grande["binario"]) == 200

    t0 = time.perf_counter()
    r_neg = conv.decimal_a_todo("-12345678901234567890")
    assert time.perf_counter() - t0 < 0.5
    assert "error" not in r_neg
    assert r_neg["decimal"].startswith("-")

    t0 = time.perf_counter()
    r_hex = conv.hexadecimal_a_todo("0x1A2B3C")
    assert time.perf_counter() - t0 < 0.5
    assert "error" not in r_hex
    assert r_hex["hexadecimal"] == "1A2B3C"


def test_render_glosa_text_casos_limite():
    texto_largo = "a" * 3000
    texto_sin_espacios = "x" * 200
    carga_xss = '<script>alert("xss")</script><img src="x" onerror="evil()">'
    codigo_matriz = "```\n" + "\n".join(" ".join(f"{i*12+j:3d}" for j in range(12)) for i in range(12)) + "\n```"

    combinado = f"{texto_largo}\n\n{texto_sin_espacios}\n\n{carga_xss}\n\n{codigo_matriz}"

    t0 = time.perf_counter()
    salida_html = render_glosa_text(combinado)
    assert time.perf_counter() - t0 < 0.1
    assert "<script" not in salida_html
    assert "<img" not in salida_html
    assert "&lt;script" in salida_html
    assert "&lt;img" in salida_html
    assert '<pre class="glosa-pre"><code>' in salida_html
    assert 'class="glosa-texto-bloque"' in salida_html
