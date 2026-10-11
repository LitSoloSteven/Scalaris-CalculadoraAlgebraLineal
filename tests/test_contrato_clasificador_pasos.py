"""Pruebas de contrato y cobertura de clasificación de pasos para resolutores."""
from fractions import Fraction
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan
from src.frontend.controladores.clasificador_pasos import clasificar_paso


def test_contrato_gauss_tres_por_tres_con_intercambio():
    """Valida la clasificación de pasos en eliminación de Gauss con intercambio forzado."""
    m = Matriz(3, 4, [
        [Fraction(0), Fraction(2), Fraction(1), Fraction(4)],
        [Fraction(3), Fraction(1), Fraction(-1), Fraction(2)],
        [Fraction(1), Fraction(-1), Fraction(2), Fraction(3)]
    ])
    resolutor = ResolutorGauss(m)
    res = resolutor.resolver()
    assert res["status"] in ("UNIQUE_SOLUTION", "SUCCESS")
    assert len(res["steps"]) > 0
    for s in res["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en Gauss 3x3 swap: '{desc}'"


def test_contrato_gauss_jordan_cuatro_por_cuatro_denso():
    """Valida la clasificación exhaustiva en Gauss-Jordan sobre matriz 4x4 densa."""
    m = Matriz(4, 5, [
        [Fraction(2), Fraction(1), Fraction(-1), Fraction(1), Fraction(8)],
        [Fraction(-3), Fraction(-1), Fraction(2), Fraction(0), Fraction(-11)],
        [Fraction(-2), Fraction(1), Fraction(2), Fraction(4), Fraction(-3)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4), Fraction(10)]
    ])
    resolutor = ResolutorGaussJordan(m)
    res = resolutor.resolver()
    assert res["status"] == "UNIQUE_SOLUTION"
    assert len(res["steps"]) > 0
    for s in res["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en GJ 4x4 denso: '{desc}'"


def test_contrato_soluciones_infinitas():
    """Valida la clasificación de pasos elementales en sistemas consistentes indeterminados."""
    m = Matriz(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(6)],
        [Fraction(3), Fraction(3), Fraction(3), Fraction(9)]
    ])
    s_gauss = ResolutorGauss(m)
    res_g = s_gauss.resolver()
    assert res_g["status"] == "INFINITE_SOLUTIONS"
    for s in res_g["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en infinitas soluciones Gauss: '{desc}'"

    m_gj = Matriz(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(3)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(6)],
        [Fraction(3), Fraction(3), Fraction(3), Fraction(9)]
    ])
    s_gj = ResolutorGaussJordan(m_gj)
    res_gj = s_gj.resolver()
    assert res_gj["status"] == "INFINITE_SOLUTIONS"
    for s in res_gj["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en infinitas soluciones GJ: '{desc}'"


def test_contrato_sin_solucion():
    """Valida la clasificación de pasos elementales en sistemas inconsistentes."""
    m = Matriz(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(5)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
    ])
    s_gauss = ResolutorGauss(m)
    res_g = s_gauss.resolver()
    assert res_g["status"] == "NO_SOLUTION"
    for s in res_g["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en sin solución Gauss: '{desc}'"

    m_gj = Matriz(3, 4, [
        [Fraction(1), Fraction(1), Fraction(1), Fraction(1)],
        [Fraction(2), Fraction(2), Fraction(2), Fraction(5)],
        [Fraction(1), Fraction(2), Fraction(3), Fraction(4)]
    ])
    s_gj = ResolutorGaussJordan(m_gj)
    res_gj = s_gj.resolver()
    assert res_gj["status"] == "NO_SOLUTION"
    for s in res_gj["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en sin solución GJ: '{desc}'"


def test_contrato_inversa_tres_por_tres():
    """Valida la clasificación de pasos en el algoritmo de inversión por Gauss-Jordan."""
    m = Matriz(3, 3, [
        [Fraction(1), Fraction(2), Fraction(3)],
        [Fraction(0), Fraction(1), Fraction(4)],
        [Fraction(5), Fraction(6), Fraction(0)]
    ])
    resolutor_inv = ResolutorInversa()
    res = resolutor_inv.resolver(m)
    assert res["status"] == "SUCCESS"
    assert len(res["steps"]) > 0
    for s in res["steps"]:
        desc = s["description"]
        clasificado = clasificar_paso(desc)
        assert clasificado["kind"] != "otro", f"Paso no clasificado en Inversa 3x3: '{desc}'"
