"""Separación de los contratos tipados de Jacobi y Gauss-Seidel."""
from collections.abc import Callable
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel import (
    EntradaGaussSeidel, resolver_gauss_seidel,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import (
    EntradaIterativa, ResultadoIterativo,
)
from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import EntradaJacobi
from src.backend.resolutores.sistemas_lineales.jacobi.jacobi import resolver_jacobi

ResolutorTipado = Callable[[object], ResultadoIterativo]


class EntradaDerivadaJacobi(EntradaJacobi):
    """Contrato propio que conserva la compatibilidad con subclases de Jacobi."""


class EntradaDerivadaGaussSeidel(EntradaGaussSeidel):
    """Contrato propio que conserva la compatibilidad con subclases de Gauss-Seidel."""


def _entrada(clase: type[EntradaIterativa]) -> EntradaIterativa:
    return clase(
        matriz_a=((4, 1), (1, 3)), vector_b=(2, 2), vector_inicial=(0, 0),
        tolerancia="1/100", maximo_iteraciones=1,
    )


@pytest.mark.parametrize("resolver,clase,nombre", [
    (resolver_jacobi, EntradaGaussSeidel, "Jacobi"),
    (resolver_jacobi, EntradaIterativa, "Jacobi"),
    (resolver_gauss_seidel, EntradaJacobi, "Gauss-Seidel"),
    (resolver_gauss_seidel, EntradaIterativa, "Gauss-Seidel"),
])
def test_los_contratos_ajenos_se_rechazan_antes_de_iterar(
    resolver: ResolutorTipado, clase: type[EntradaIterativa], nombre: str,
) -> None:
    """El otro método y la clase base no satisfacen el contrato tipado del resolutor."""
    resultado = resolver(_entrada(clase))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.aproximacion is None
    assert resultado.entrada_canonica is None
    assert resultado.pasos == ()
    assert resultado.diagnostico is not None
    assert resultado.diagnostico.campo == "entrada"
    assert nombre in resultado.diagnostico.mensaje


@pytest.mark.parametrize("resolver,clase,aproximacion", [
    (resolver_jacobi, EntradaJacobi, (Fraction(1, 2), Fraction(2, 3))),
    (resolver_jacobi, EntradaDerivadaJacobi, (Fraction(1, 2), Fraction(2, 3))),
    (resolver_gauss_seidel, EntradaGaussSeidel, (Fraction(1, 2), Fraction(1, 2))),
    (resolver_gauss_seidel, EntradaDerivadaGaussSeidel, (Fraction(1, 2), Fraction(1, 2))),
])
def test_el_contrato_propio_y_sus_subclases_conservan_su_metodo(
    resolver: ResolutorTipado, clase: type[EntradaIterativa], aproximacion: tuple[Fraction, ...],
) -> None:
    """Las entradas del método mantienen la secuencia de actualización correspondiente."""
    resultado = resolver(_entrada(clase))

    assert resultado.codigo == "MAXIMO_ITERACIONES"
    assert resultado.aproximacion == aproximacion
    assert resultado.iteraciones_realizadas == 1
