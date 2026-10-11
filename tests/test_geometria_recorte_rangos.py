"""Rangos automáticos y recorte de rectas al área visible."""
from src.backend.geometria.recorte import calcular_rango_automatico, recortar_recta_a_caja


def test_rango_automatico_simetrico():
    """El rango cubre ambos signos con la misma extensión."""
    rango = calcular_rango_automatico([3.0, -2.0])
    assert rango[0] == -rango[1]
    assert rango[1] >= 3.0


def test_rango_automatico_minimo():
    """Los valores pequeños conservan un área visible mínima."""
    rango = calcular_rango_automatico([0.5])
    assert rango[1] >= 5.0


def test_rango_automatico_escala_125():
    """El margen de escala se redondea al rango esperado."""
    rango = calcular_rango_automatico([7.0])
    assert rango == [-10.0, 10.0]


def test_rango_automatico_sin_finitos():
    """Los valores no finitos usan el rango predeterminado."""
    rango = calcular_rango_automatico([float("inf"), float("-inf"), float("nan")])
    assert rango == [-5.0, 5.0]


def test_rango_automatico_vacio():
    """Una colección vacía tiene rango definido."""
    rango = calcular_rango_automatico([])
    assert rango == [-5.0, 5.0]


def test_rango_automatico_valores_nulos():
    """Los valores nulos no alteran la simetría."""
    rango = calcular_rango_automatico([None, 3.0, None])
    assert rango[0] == -rango[1]


def test_rango_automatico_tope_grande():
    """Los valores extremos respetan el tope de visualización."""
    rango = calcular_rango_automatico([1e15])
    assert rango[1] <= 1e6


def test_recorte_recta_caja_interior():
    """Una recta desde el interior alcanza ambos bordes."""
    resultado = recortar_recta_a_caja([0.0, 0.0], [1.0, 0.0], 5.0)
    assert resultado is not None
    assert abs(resultado[0] - (-5.0)) < 1e-6
    assert abs(resultado[1] - 5.0) < 1e-6


def test_recorte_recta_caja_exterior_cruce():
    """El origen exterior conserva los parámetros de cruce correctos."""
    resultado = recortar_recta_a_caja([10.0, 0.0], [1.0, 0.0], 5.0)
    assert resultado is not None
    assert abs(resultado[0] - (-15.0)) < 1e-6
    assert abs(resultado[1] - (-5.0)) < 1e-6


def test_recorte_recta_caja_paralela_exterior():
    """Una recta paralela fuera de la caja no tiene segmento visible."""
    resultado = recortar_recta_a_caja([0.0, 10.0], [1.0, 0.0], 5.0)
    assert resultado is None


def test_recorte_recta_caja_direccion_cero():
    """Una dirección nula no genera un segmento."""
    resultado = recortar_recta_a_caja([0.0, 0.0], [0.0, 0.0], 5.0)
    assert resultado is None
