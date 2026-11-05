"""Validación estricta de criterios, tolerancias y compatibilidad de capturas."""
import math
from dataclasses import asdict
from fractions import Fraction

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion, validar_entrada
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada


def _datos(criterio=None, limite=100):
    return dict(expresion="x**2-2", extremo_izquierdo=1, extremo_derecho=2,
                decimales=4, limite_iteraciones=limite, criterio=criterio)


@pytest.mark.parametrize("tipo", ["relativo", "ancho", "residuo"])
@pytest.mark.parametrize("valor", [True, False, None, "0.01", 0, -1, math.nan,
                                     math.inf, -math.inf, 1e-400, 10**400, 1j])
def test_tolerancias_invalidas_se_rechazan(tipo, valor):
    """Los campos no se convierten a cero ni admiten magnitudes no representables."""
    with pytest.raises(ValueError):
        validar_entrada(_datos(CriterioParada(tipo, valor)))


@pytest.mark.parametrize("tipo", ["decimales", "iteraciones"])
@pytest.mark.parametrize("valor", [True, False, 2.0, 2.5, "2", None, math.inf, math.nan, -1])
def test_enteros_no_admiten_booleanos_ni_truncamiento(tipo, valor):
    """Un float integral tampoco sustituye el entero requerido por el contrato del dominio."""
    with pytest.raises(ValueError):
        validar_entrada(_datos(CriterioParada(tipo, valor)))


@pytest.mark.parametrize("criterio", [
    {}, {"tipo": "ancho"}, {"tipo": "ancho", "parametro": .01, "otro": 1},
    [], "ancho", {"tipo": [], "parametro": .01}, {"tipo": "otro", "parametro": .01},
])
def test_carga_de_criterio_malformada_no_llega_al_motor(criterio):
    """Los nombres y estructuras ajenos al contrato producen errores controlados."""
    with pytest.raises(ValueError):
        validar_entrada(_datos(criterio))


@pytest.mark.parametrize("parametro,limite", [(0, 100), (101, 100), (501, 500)])
def test_n_fijo_no_se_recorta_al_limite(parametro, limite):
    """El presupuesto de seguridad independiente rechaza un conteo solicitado excesivo."""
    with pytest.raises(ValueError):
        validar_entrada(_datos(CriterioParada("iteraciones", parametro), limite))


def test_limites_decimal_y_de_seguridad_se_conservan():
    """Mantiene d hasta quince y un máximo de quinientas filas en el dominio."""
    entrada = validar_entrada(_datos(CriterioParada("decimales", 15), 500))
    assert entrada.criterio.umbral == Fraction(1, 10**15)
    with pytest.raises(ValueError):
        validar_entrada(_datos(CriterioParada("decimales", 16)))
    with pytest.raises(ValueError):
        validar_entrada(_datos(CriterioParada("iteraciones", 1), 501))


@pytest.mark.parametrize("tipo", ["relativo", "ancho", "residuo"])
def test_menor_tolerancia_representable_sigue_siendo_positiva(tipo):
    """La validación conserva un subnormal finito sin convertirlo en una tolerancia cero."""
    entrada = validar_entrada(_datos(CriterioParada(tipo, math.ulp(0.0))))
    assert entrada.criterio.umbral == math.ulp(0.0)


def test_contrato_posicional_y_serializacion_de_entrada():
    """Los cinco argumentos previos siguen operativos y el criterio soporta ida y vuelta."""
    antiguo = EntradaBiseccion("x**2-2", 1, 2, 2, 100)
    canonico = validar_entrada(asdict(antiguo))
    assert canonico.criterio == CriterioParada("decimales", 2)
    assert canonico.error_absoluto == Fraction(1, 100)
    assert validar_entrada(asdict(canonico)) == canonico


def test_precision_visual_no_sustituye_parametro_del_criterio():
    """El decimal explícito usa su d mientras el formato visual permanece independiente."""
    entrada = validar_entrada(_datos(CriterioParada("decimales", 2)))
    assert entrada.decimales == 4
    assert entrada.error_absoluto == Fraction(1, 100)
    assert entrada.criterio.parametro == 2


def test_motor_revalida_criterios_de_entradas_directas():
    """Crear un dataclass no evita el rechazo de n excesivo en el servicio público."""
    entrada = EntradaBiseccion("x", -1, 2, 4, criterio=CriterioParada("iteraciones", 101))
    resultado = biseccion(entrada)
    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "ENTRADA_INVALIDA"
    assert not resultado.iteraciones


@pytest.mark.parametrize("decimales", [True, 16, 100_000_000])
def test_umbral_decimal_directo_valida_antes_de_calcular_potencias(decimales):
    """Inspeccionar un criterio inválido no admite booleanos ni reserva una potencia desmesurada."""
    with pytest.raises(ValueError):
        _ = CriterioParada("decimales", decimales).umbral
