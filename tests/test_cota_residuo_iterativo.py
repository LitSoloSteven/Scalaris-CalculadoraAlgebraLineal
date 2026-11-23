"""Residuos exactos con una cota de bits independiente de las aproximaciones."""
from collections.abc import Callable
from fractions import Fraction
from types import ModuleType

import pytest

import src.backend.resolutores.sistemas_lineales.gauss_seidel.gauss_seidel as motor_gauss_seidel
import src.backend.resolutores.sistemas_lineales.jacobi.jacobi as motor_jacobi
from src.backend.resolutores.sistemas_lineales.gauss_seidel.limites_gauss_seidel import (
    CONFIGURACION_ARITMETICA_GAUSS_SEIDEL,
)
from src.backend.resolutores.sistemas_lineales.iterativos.aritmetica_iterativa import (
    ConfiguracionAritmetica, LimiteResiduoIterativo, PresupuestoAritmetico, residuo_sistema,
)
from src.backend.resolutores.sistemas_lineales.iterativos.contrato_iterativo import ResultadoIterativo

ResolutorCaptura = Callable[[object], ResultadoIterativo]
Metodo = tuple[ModuleType, ResolutorCaptura]
METODOS = (
    (motor_gauss_seidel, motor_gauss_seidel.resolver_gauss_seidel_desde_captura),
    (motor_jacobi, motor_jacobi.resolver_jacobi_desde_captura),
)
_COEFICIENTE = Fraction(1, 2 ** 2050)
_COMPLEMENTO = 1 - _COEFICIENTE
_RESIDUO_GRANDE = -_COEFICIENTE * _COMPLEMENTO
_VECTORES = ((_COMPLEMENTO, 0), (0, _COMPLEMENTO), (-_COMPLEMENTO, _COMPLEMENTO))
_RESIDUOS = ((_RESIDUO_GRANDE, _COMPLEMENTO), (_RESIDUO_GRANDE, 0), (0, 0))


def _captura(maximo: int = 2) -> dict[str, object]:
    return {
        "matriz_a": [[_COEFICIENTE, _COEFICIENTE], [0, 1]],
        "vector_b": [0, _COMPLEMENTO], "vector_inicial": [_COMPLEMENTO, 0],
        "tolerancia": _COEFICIENTE / 2, "maximo_iteraciones": maximo,
    }


@pytest.mark.parametrize("metodo", METODOS)
def test_un_residuo_intermedio_grande_no_impide_llegar_a_la_solucion(metodo: Metodo) -> None:
    """El primer paso conserva (0, c) y el segundo certifica (-c, c) con residuo cero."""
    modulo, resolver = metodo
    resultado = resolver(_captura())

    assert _RESIDUO_GRANDE.denominator.bit_length() == 4101
    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == _VECTORES[2]
    assert resultado.residuo == _RESIDUOS[2]
    assert resultado.iteraciones_realizadas == 2
    primero, segundo = resultado.pasos
    assert primero.vector_nuevo == _VECTORES[1]
    assert primero.norma_residuo == -_RESIDUO_GRANDE
    assert segundo.vector_anterior == primero.vector_nuevo
    assert segundo.norma_residuo == 0


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("escalar", [False, True])
def test_la_tolerancia_inicial_se_certifica_con_un_residuo_de_mas_bits(
    metodo: Metodo, escalar: bool,
) -> None:
    """Un residuo menor que la tolerancia se certifica antes de ejecutar cualquier barrido."""
    modulo, resolver = metodo
    captura = _captura()
    captura.update(vector_inicial=[0, _COMPLEMENTO], tolerancia=_COEFICIENTE)
    esperado = -_RESIDUO_GRANDE
    if escalar:
        captura.update(matriz_a=[[_COEFICIENTE]], vector_b=[0], vector_inicial=[_COEFICIENTE])
        esperado = _COEFICIENTE ** 2
    resultado = resolver(captura)

    assert resultado.codigo == "TOLERANCIA_ALCANZADA"
    assert resultado.iteraciones_realizadas == 0
    assert resultado.pasos == ()
    assert resultado.norma_residuo == esperado
    assert esperado.denominator.bit_length() == 4101
    assert "tras 0 barridos" in resultado.explicacion


@pytest.mark.parametrize("metodo", METODOS)
@pytest.mark.parametrize("caso", [
    (27, 1, "LIMITE_ARITMETICO", 0), (28, 1, "MAXIMO_ITERACIONES", 1),
    (45, 2, "LIMITE_ARITMETICO", 1), (46, 2, "SOLUCION_EXACTA", 2),
])
def test_la_cota_del_residuo_conserva_los_cargos_y_los_barridos_verificados(
    metodo: Metodo, monkeypatch: pytest.MonkeyPatch, caso: tuple[int, int, str, int],
) -> None:
    """Los cargos 28 y 46 siguen siendo necesarios para verificar el primer y segundo paso."""
    modulo, resolver = metodo
    operaciones, maximo, codigo, iteraciones = caso
    presupuesto = PresupuestoAritmetico(CONFIGURACION_ARITMETICA_GAUSS_SEIDEL, operaciones)
    monkeypatch.setattr(modulo, "PresupuestoAritmetico", lambda *argumentos: presupuesto)
    resultado = resolver(_captura(maximo))

    assert resultado.codigo == codigo
    assert resultado.iteraciones_realizadas == iteraciones
    assert resultado.aproximacion == _VECTORES[iteraciones]
    assert resultado.residuo == _RESIDUOS[iteraciones]
    assert resultado.norma_residuo == max(abs(valor) for valor in _RESIDUOS[iteraciones])
    assert presupuesto.restantes == (0 if operaciones in (28, 46) else -1)


def test_la_cota_propia_admite_un_residuo_mayor_que_la_cota_del_vector() -> None:
    """El residuo 4567/15015 se verifica sin relajar los cuatro bits de las componentes."""
    configuracion = ConfiguracionAritmetica(
        maximo_operaciones=10, maximo_bits_entrada=4, maximo_bits_calculo=4,
        maximo_bits_cambio=10, maximo_bits_acumulacion=64,
    )
    presupuesto = PresupuestoAritmetico(configuracion)
    residuo = residuo_sistema(
        ((Fraction(1, 13), Fraction(1, 11)), (Fraction(0), Fraction(1))),
        (Fraction(1, 3), Fraction(1, 5)), (Fraction(1, 7), Fraction(1, 5)), presupuesto,
    )

    assert residuo == (Fraction(4567, 15015), Fraction(0))
    assert residuo[0].denominator.bit_length() > configuracion.maximo_bits_calculo
    assert residuo[0].denominator.bit_length() <= configuracion.maximo_bits_residuo
    assert presupuesto.restantes == 0


def test_la_cota_del_residuo_sigue_rechazando_valores_fuera_del_presupuesto() -> None:
    """Una llamada aritmética con b fuera de contrato no elimina la cota finita del residuo."""
    configuracion = ConfiguracionAritmetica(
        maximo_operaciones=3, maximo_bits_entrada=4, maximo_bits_calculo=4,
        maximo_bits_cambio=10, maximo_bits_acumulacion=8,
    )
    presupuesto = PresupuestoAritmetico(configuracion)
    fuera_de_cota = Fraction(2 ** configuracion.maximo_bits_residuo)

    with pytest.raises(LimiteResiduoIterativo):
        residuo_sistema(((Fraction(1),),), (fuera_de_cota,), (Fraction(0),), presupuesto)
    assert presupuesto.restantes == 0
