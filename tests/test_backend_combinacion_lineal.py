"""Pruebas de dominio para combinación lineal y operaciones vectoriales."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores
from tests.comun_combinacion import preparar_combinacion_canonica


def test_combinacion_lineal_flujo_canonico():
    """Valida el ejemplo canónico de Lay en R³."""
    resolutor, a1, a2, b, res = preparar_combinacion_canonica()

    assert res["estado"] == "UNICA"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3), Fraction(2)]
    assert res["coeficientes_texto"] == ["3", "2"]
    assert len(res["pasos_planteamiento"]) == 5

    assert "1. Ecuación vectorial" in res["pasos_planteamiento"][0]["descripcion"]
    assert "2. Multiplicación de los escalares" in res["pasos_planteamiento"][1]["descripcion"]
    assert "3. Suma vectorial" in res["pasos_planteamiento"][2]["descripcion"]
    assert "4. Sistema de ecuaciones lineales" in res["pasos_planteamiento"][3]["descripcion"]
    assert "5. Matriz aumentada" in res["pasos_planteamiento"][4]["descripcion"]

    paso_verificacion = res["paso_verificacion"]
    assert paso_verificacion is not None
    assert paso_verificacion["coincide"] is True
    assert r"\checkmark" in paso_verificacion["detalle_latex"]


def test_combinacion_lineal_coeficientes_fraccionarios():
    """Valida combinación lineal con coeficientes fraccionarios exactos."""
    v1 = Matriz(2, 1, [[2], [0]])
    v2 = Matriz(2, 1, [[0], [3]])
    b = Matriz(2, 1, [[1], [1]])

    resolutor = ResolutorCombinacionLineal()
    res = resolutor.resolver(
        b,
        [v1, v2],
        nombres_variables=["c_1", "c_2"],
        nombres_vectores=["v_1", "v_2"],
    )

    assert res["estado"] == "UNICA"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(1, 2), Fraction(1, 3)]
    assert res["coeficientes_texto"] == ["1/2", "1/3"]
    assert res["paso_verificacion"]["coincide"] is True


def test_combinacion_lineal_un_solo_vector():
    """Valida combinación lineal con un único vector (k=1)."""
    v1 = Matriz(3, 1, [[2], [4], [6]])
    b = Matriz(3, 1, [[6], [12], [18]])

    resolutor = ResolutorCombinacionLineal()
    res = resolutor.resolver(b, [v1], nombres_variables=["c_1"], nombres_vectores=["v_1"])

    assert res["estado"] == "UNICA"
    assert res["es_combinacion_lineal"] is True
    assert res["coeficientes"] == [Fraction(3)]
    assert res["paso_verificacion"]["coincide"] is True


def test_operaciones_vectores_vector_completo():
    """Valida que suma, resta y escalar retornen el vector resultante completo."""
    resolutor = ResolutorOperacionesVectores()
    v1 = Matriz(3, 1, [[1], [-2], [5]])
    v2 = Matriz(3, 1, [[3], [4], [-1]])

    resultado_suma = resolutor.sumar(v1, v2, nombre1="v_1", nombre2="v_2")
    assert resultado_suma["estado"] == "EXITO"
    assert "vector_resultado_latex" in resultado_suma
    assert resultado_suma["detalles_latex"][-1] == resultado_suma["vector_resultado_latex"]

    resultado_resta = resolutor.restar(v1, v2, nombre1="v_1", nombre2="v_2")
    assert resultado_resta["estado"] == "EXITO"
    assert resultado_resta["detalles_latex"][-1] == resultado_resta["vector_resultado_latex"]

    res_esc = resolutor.multiplicar_escalar(-3, v1, nombre="v", nombre_resultado="w")
    assert res_esc["estado"] == "EXITO"
    assert res_esc["detalles_latex"][-1] == res_esc["vector_resultado_latex"]
