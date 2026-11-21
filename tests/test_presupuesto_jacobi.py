"""Comprobaciones del presupuesto del resolutor en el límite de la traza."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.jacobi import aritmetica_jacobi
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi_desde_captura


@pytest.mark.parametrize("operaciones,codigo,aproximacion", [
    (7, "LIMITE_ARITMETICO", (0,)),
    (8, "SOLUCION_EXACTA", (1,)),
])
def test_el_presupuesto_debe_alcanzar_para_verificar_el_residuo(
    monkeypatch: pytest.MonkeyPatch, operaciones: int, codigo: str, aproximacion: tuple[int, ...],
) -> None:
    """Verificar el residuo requiere ocho cargos y basta para publicar la solución y su paso."""
    monkeypatch.setattr(aritmetica_jacobi, "MAXIMO_OPERACIONES_JACOBI", operaciones)
    resultado = resolver_jacobi_desde_captura({
        "matriz_a": [[1]], "vector_b": [1], "tolerancia": "1/100", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == codigo
    assert resultado.aproximacion == aproximacion
    assert resultado.residuo == (1 - aproximacion[0],)
    assert resultado.iteraciones_realizadas == aproximacion[0]
    if resultado.pasos:
        assert resultado.pasos[0].norma_cambio == 1


def test_la_traza_conserva_la_tolerancia_certificada_con_el_ultimo_cargo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Al cumplir la tolerancia con el último cargo se publica el paso completo."""
    monkeypatch.setattr(aritmetica_jacobi, "MAXIMO_OPERACIONES_JACOBI", 28)
    resultado = resolver_jacobi_desde_captura({
        "matriz_a": [[4, 1], [1, 3]], "vector_b": [2, 2],
        "tolerancia": "2/3", "maximo_iteraciones": 1,
    })

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.aproximacion == (Fraction(1, 2), Fraction(2, 3))
    assert resultado.iteraciones_realizadas == 1
    assert resultado.pasos[0].norma_cambio == resultado.norma_residuo == Fraction(2, 3)
