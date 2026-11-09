"""Caracterización de la captura compartida y su fachada de bisección."""
import math

import pytest

from src.frontend.controladores import captura_real
from src.frontend.controladores.biseccion import captura_criterio
from tests.comun_biseccion_criterios import captura_criterio as crear_captura


def test_fachada_conserva_las_conversiones_publicas():
    """Los consumidores antiguos y nuevos importan exactamente las mismas funciones."""
    assert captura_criterio.entero_capturado is captura_real.entero_capturado
    assert captura_criterio.real_capturado is captura_real.real_capturado


@pytest.mark.parametrize("valor,esperado", [
    (" 1e2 ", 100), ("100.0", 100), (0, 0), (-2.0, -2),
    ("9007199254740993", 9007199254740993),
])
def test_enteros_conservan_valor_exacto_del_texto(valor, esperado):
    """La notación científica y enteros grandes no se truncan al pasar por float."""
    assert captura_real.entero_capturado(valor, "El límite") == esperado


@pytest.mark.parametrize("valor", [
    True, False, None, "", "1/2", "abc", "nan", "inf", "1e309", 1.2,
    "1.0000000000000001", "9007199254740992.5", [], {},
])
def test_enteros_invalidos_conservan_mensaje_y_rechazo(valor):
    """Incluye decimales que float redondearía a entero y datos no finitos."""
    with pytest.raises(ValueError, match=r"^El límite debe ser un entero\.$"):
        captura_real.entero_capturado(valor, "El límite")


@pytest.mark.parametrize("valor,esperado", [(" 1e-6 ", 1e-6), ("-0", -0.0), (2, 2.0)])
def test_reales_conservan_conversion_lexica(valor, esperado):
    """Admite punto decimal y notación científica sin imponer tolerancia de dominio."""
    assert captura_real.real_capturado(valor, "El extremo") == esperado


@pytest.mark.parametrize("valor", [True, False, None, "", "1/2", "1,5", "abc", [], {}])
def test_reales_invalidos_orientan_sin_exponer_el_valor(valor):
    """Los errores conservan la etiqueta y la indicación del separador decimal."""
    with pytest.raises(ValueError) as error:
        captura_real.real_capturado(valor, "El extremo")
    assert str(error.value) == "El extremo debe ser un número real. Usa un punto para los decimales."


@pytest.mark.parametrize("valor", ["nan", "inf", "-inf", "1e309"])
def test_finitud_permanece_en_el_contrato_del_dominio(valor):
    """La extracción no cambia la separación entre conversión y validez matemática."""
    assert not math.isfinite(captura_real.real_capturado(valor, "El extremo"))
    captura = crear_captura() | {"extremo_izquierdo": valor}
    with pytest.raises(ValueError):
        captura_criterio.preparar_entrada(captura)


def test_intervalo_invertido_y_criterio_conservan_el_contrato():
    """El dominio ordena los extremos y recibe el criterio numérico convertido."""
    captura = crear_captura("residuo", "1e-6")
    captura.update(extremo_izquierdo="2", extremo_derecho="1")
    entrada = captura_criterio.preparar_entrada(captura)
    assert (entrada.extremo_izquierdo, entrada.extremo_derecho) == (1, 2)
    assert entrada.intervalo_invertido
    assert entrada.criterio.tipo == "residuo" and entrada.criterio.parametro == 1e-6
