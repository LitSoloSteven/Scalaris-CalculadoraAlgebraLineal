"""Intervalos canónicos, avisos persistentes y rechazo de extremos inválidos."""
import json
import math
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import (
    AVISO_INTERVALO_INVERTIDO, EntradaBiseccion, validar_entrada,
)
from src.frontend.controladores.biseccion.controlador import resolver_captura
from tests.comun_biseccion_criterios import captura_criterio


def _datos():
    return {"expresion": "x**2-2", "extremo_izquierdo": 2, "extremo_derecho": 1, "decimales": 4}


def test_validacion_invertida_es_idempotente_y_no_muta_carga():
    """El aviso sobrevive al transporte del dataclass y a la validación del propio motor."""
    datos = _datos()
    entrada = validar_entrada(datos)
    assert datos == _datos()
    assert (entrada.extremo_izquierdo, entrada.extremo_derecho) == (1, 2)
    assert entrada.intervalo_invertido is True
    assert entrada.advertencias == (AVISO_INTERVALO_INVERTIDO,)
    for _ in range(3):
        entrada = validar_entrada(asdict(entrada))
        assert entrada.advertencias == (AVISO_INTERVALO_INVERTIDO,)
    assert biseccion(entrada).advertencias == (AVISO_INTERVALO_INVERTIDO,)
    json.dumps(asdict(entrada), allow_nan=False)


@pytest.mark.parametrize("tipo,parametro", [
    ("decimales", 2), ("ancho", ".01"), ("relativo", "1"), ("residuo", ".1"), ("iteraciones", 3),
])
def test_inversion_no_altera_calculo_ni_criterio(tipo, parametro):
    """Todos los criterios generan la misma traza que el intervalo ya ordenado."""
    captura = captura_criterio(tipo, parametro)
    normal = resolver_captura(captura)
    invertida = resolver_captura({**captura, "extremo_izquierdo": "2", "extremo_derecho": "1"})
    for clave in ("estado", "mensaje", "aproximacion", "intervalo_final", "iteraciones", "motivo_parada",
                  "codigo_diagnostico", "diagnostico", "criterio_solicitado", "umbral", "metrica_final"):
        assert invertida[clave] == normal[clave]
    assert invertida["entrada"]["extremo_izquierdo"] == 1
    assert invertida["entrada"]["extremo_derecho"] == 2
    assert invertida["advertencias"] == (AVISO_INTERVALO_INVERTIDO,)
    assert normal["advertencias"] == ()
    json.dumps(invertida, allow_nan=False)


@pytest.mark.parametrize("extremos", [(1, 1), (0.0, -0.0)])
def test_extremos_iguales_siguen_rechazados(extremos):
    """La normalización no convierte un punto en intervalo de bisección."""
    with pytest.raises(ValueError, match="intervalo es inválido"):
        validar_entrada({**_datos(), "extremo_izquierdo": extremos[0], "extremo_derecho": extremos[1]})


@pytest.mark.parametrize("valor", [None, "", " ", "1", True, False, math.nan, math.inf, -math.inf, 1j, 10**400])
@pytest.mark.parametrize("campo", ["extremo_izquierdo", "extremo_derecho"])
def test_dominio_rechaza_extremos_invalidos_sin_convertirlos_a_cero(campo, valor):
    """El dominio no usa conversiones permisivas ni ordena valores inválidos."""
    with pytest.raises(ValueError):
        validar_entrada({**_datos(), campo: valor})


@pytest.mark.parametrize("valor", [None, "", " ", "nan", "inf", "-inf", True])
def test_captura_invalida_no_se_normaliza_como_cero(valor):
    """La adaptación de campos vacíos o no finitos conserva un error visible."""
    respuesta = resolver_captura({**captura_criterio(), "extremo_izquierdo": valor})
    assert respuesta["estado"] == "ERROR"
    assert respuesta.get("aproximacion") is None


@pytest.mark.parametrize("valor", [None, "si", 1, [], {}])
def test_marca_de_intercambio_solo_admite_booleanos(valor):
    """La metadata del transporte se revalida sin aceptar coerciones o texto libre."""
    with pytest.raises(ValueError, match="booleana"):
        validar_entrada({**_datos(), "intervalo_invertido": valor})


def test_inversion_conserva_avisos_incluso_si_hay_error_o_cero_extremo():
    """La normalización se comunica tanto al fallar sintaxis como al hallar un cero junto a un polo."""
    error = biseccion(EntradaBiseccion("sin()", 2, 1, 4))
    assert error.estado == "ERROR"
    assert error.advertencias == (AVISO_INTERVALO_INVERTIDO,)
    cero = biseccion(EntradaBiseccion("(x-1)/(x-0.1234)", 1, -1, 4))
    assert cero.estado == "EXITO"
    assert cero.aproximacion == 1
    assert cero.iteraciones == ()
    assert cero.advertencias[0] == AVISO_INTERVALO_INVERTIDO
    assert any("Continuidad no certificada" in aviso for aviso in cero.advertencias)
    assert cero.diagnostico["codigo"] == "SINGULARIDAD_DETECTADA"
    json.dumps(asdict(cero), default=str, allow_nan=False)
