"""Pruebas de robustez y rendimiento ante datos límite y entradas extremas."""
from tests.comun_entradas import copiar_entrada_prueba
import json
import time
from fractions import Fraction
import pytest

from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    CalculadoraRomana,
    ErrorNumeroRomano,
)
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.componentes.glosa_renderizado import renderizar_texto_glosa
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
    """Verifica entradas celdas extremas e invalidas."""
    casos = [
        ("1001/1000", True),
        ("-123456789012/987654321", True),
        ("0.0000001", True),
        ("1/0", False),
        ("abc", False),
        ("", False),
    ]

    for valor_cadena, debe_ser_valido in casos:
        t0 = time.perf_counter()
        ok, parseado, mensaje_error = ValidadorMatriz.parsear_numero_exacto(valor_cadena)
        duracion = time.perf_counter() - t0

        assert duracion < 0.05
        assert ok is debe_ser_valido
        assert isinstance(parseado, Fraction)
        assert "Traceback" not in mensaje_error
        if not ok:
            assert len(mensaje_error) > 0


def test_controlador_geometria_los_tres_procesos():
    """Verifica controlador geometria los tres procesos."""
    p_rectas = json.dumps({
        "matriz_a": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
    })
    t0 = time.perf_counter()
    r_rectas = ControladorGeometria.procesar_rectas_planos(p_rectas)
    assert time.perf_counter() - t0 < 1.0
    assert r_rectas.get("estado") == "EXITO"
    assert "Traceback" not in r_rectas.get("mensaje", "")
    json.dumps(r_rectas)

    p_vecs = json.dumps(copiar_entrada_prueba('vectores_plano'))
    t0 = time.perf_counter()
    r_vecs = ControladorGeometria.procesar_vectores(p_vecs)
    assert time.perf_counter() - t0 < 1.0
    assert r_vecs.get("estado") == "EXITO"
    assert "Traceback" not in r_vecs.get("mensaje", "")
    json.dumps(r_vecs)

    p_comb = json.dumps(copiar_entrada_prueba('combinacion_plano'))
    t0 = time.perf_counter()
    r_comb = ControladorGeometria.procesar_combinacion(p_comb)
    assert time.perf_counter() - t0 < 1.0
    assert r_comb.get("estado") == "EXITO"
    assert "Traceback" not in r_comb.get("mensaje", "")
    json.dumps(r_comb)


def test_controlador_inversas_cincuenta_por_cincuenta_identidad():
    """Verifica controlador inversas cincuenta por cincuenta identidad."""
    n = 50
    mat_ident = [[("1/2" if i == j else "0") for j in range(n)] for i in range(n)]
    carga = json.dumps({"dimension": n, "datos": mat_ident})

    t0 = time.perf_counter()
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert time.perf_counter() - t0 < 30.0
    assert res.get("estado") == "EXITO"
    assert "Traceback" not in res.get("mensaje", "")
    assert res.get("dimension") == 50


def test_controlador_inversas_cincuenta_por_cincuenta_singular():
    """Verifica controlador inversas cincuenta por cincuenta singular."""
    n = 50
    mat_sing = [[("1" if i == j else "0") for j in range(n)] for i in range(n)]
    mat_sing[1] = list(mat_sing[0])
    carga = json.dumps({"dimension": n, "datos": mat_sing})

    t0 = time.perf_counter()
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert time.perf_counter() - t0 < 0.5
    assert res.get("estado") == "SINGULAR"
    assert "Traceback" not in res.get("mensaje", "")
    assert res.get("dimension") == 50


def test_sistemas_lineales_diez_por_diez_inconsistente():
    """Verifica sistemas lineales diez por diez inconsistente."""
    mat_10 = [["1" if i == j else "0" for j in range(10)] for i in range(10)]
    mat_10[9] = ["0"] * 10
    b_10 = ["1"] * 9 + ["5"]
    carga = json.dumps({"matriz_a": mat_10, "vector_b": b_10})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 1.0
    assert res_gauss.get("estado") == "SIN_SOLUCION"

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 1.0
    assert res_gj.get("estado") == "SIN_SOLUCION"


def test_sistemas_lineales_uno_por_uno():
    """Verifica sistemas lineales uno por uno."""
    carga = json.dumps({"matriz_a": [["2"]], "vector_b": ["6"]})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 0.5
    assert res_gauss.get("estado") == "SOLUCION_UNICA"
    assert res_gauss.get("solucion") == ["3"]

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 0.5
    assert res_gj.get("estado") == "SOLUCION_UNICA"
    assert res_gj.get("solucion") == ["3"]


def test_sistemas_lineales_diez_por_uno():
    """Verifica sistemas lineales diez por uno."""
    mat = [[str(i + 1)] for i in range(10)]
    b = [str((i + 1) * 2) for i in range(10)]
    carga = json.dumps({"matriz_a": mat, "vector_b": b})

    t0 = time.perf_counter()
    res_gauss = json.loads(ControladorGauss.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 0.5
    assert res_gauss.get("estado") == "SOLUCION_UNICA"
    assert res_gauss.get("solucion") == ["2"]

    t0 = time.perf_counter()
    res_gj = json.loads(ControladorGaussJordan.procesar_sistema(carga))
    assert time.perf_counter() - t0 < 0.5
    assert res_gj.get("estado") == "SOLUCION_UNICA"
    assert res_gj.get("solucion") == ["2"]


def test_combinacion_lineal_vectores_diez_dimensiones():
    """Verifica combinacion lineal vectores diez dimensiones."""
    b_v = {"datos": [str(i + 1) for i in range(10)], "orientacion": "columna"}
    vectores_nueve = [
        {"datos": [("1" if i == j else "0") for i in range(10)], "orientacion": "columna"}
        for j in range(9)
    ]
    carga = json.dumps({"objetivo": b_v, "vectores": vectores_nueve})

    t0 = time.perf_counter()
    res = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga))
    assert time.perf_counter() - t0 < 2.0
    assert res.get("estado") in ("SIN_SOLUCION", "UNICA", "INFINITA")
    assert "Traceback" not in res.get("mensaje", "")


def test_calculadora_romana_desbordamiento_y_cero():
    """Verifica calculadora romana desbordamiento y cero."""
    t0 = time.perf_counter()
    try:
        CalculadoraRomana.sumar("MMMCMXCIX", "I")
        error_suma = None
    except (ErrorNumeroRomano, ValueError) as e:
        error_suma = str(e)
    assert time.perf_counter() - t0 < 0.1
    assert error_suma is not None
    assert "Traceback" not in error_suma

    t0 = time.perf_counter()
    try:
        CalculadoraRomana.restar("V", "V")
        error_resta = None
    except (ErrorNumeroRomano, ValueError) as e:
        error_resta = str(e)
    assert time.perf_counter() - t0 < 0.1
    assert error_resta is not None
    assert "cero" in error_resta.lower()


def test_conversor_bases_enteros_grandes_y_negativos():
    """Verifica conversor bases enteros grandes y negativos."""
    conv = ConversorBases()
    valor_grande = str(2 ** 200 - 1)
    t0 = time.perf_counter()
    r_grande = conv.decimal_a_todo(valor_grande)
    assert time.perf_counter() - t0 < 0.5
    assert "mensaje" not in r_grande
    assert len(r_grande["binario"]) == 200

    t0 = time.perf_counter()
    r_neg = conv.decimal_a_todo("-12345678901234567890")
    assert time.perf_counter() - t0 < 0.5
    assert "mensaje" not in r_neg
    assert r_neg["decimal"].startswith("-")

    t0 = time.perf_counter()
    r_hex = conv.hexadecimal_a_todo("0x1A2B3C")
    assert time.perf_counter() - t0 < 0.5
    assert "mensaje" not in r_hex
    assert r_hex["hexadecimal"] == "1A2B3C"


def test_renderizado_glosa_texto_casos_limite():
    """Verifica el renderizado de Glosa con textos desfavorables."""
    texto_largo = "a" * 3000
    texto_sin_espacios = "x" * 200
    carga_xss = '<script>alert("xss")</script><img src="x" onerror="evil()">'
    codigo_matriz = "```\n" + "\n".join(" ".join(f"{i*12+j:3d}" for j in range(12)) for i in range(12)) + "\n```"

    combinado = f"{texto_largo}\n\n{texto_sin_espacios}\n\n{carga_xss}\n\n{codigo_matriz}"

    t0 = time.perf_counter()
    salida_html = renderizar_texto_glosa(combinado)
    assert time.perf_counter() - t0 < 0.1
    assert "<script" not in salida_html
    assert "<img" not in salida_html
    assert "&lt;script" in salida_html
    assert "&lt;img" in salida_html
    assert '<pre class="glosa-pre"><code>' in salida_html
    assert 'class="glosa-texto-bloque"' in salida_html
