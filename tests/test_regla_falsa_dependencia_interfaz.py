"""Comprobación del contrato real que consumirá la presentación de regla falsa."""
import json
import math
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.regla_falsa import regla_falsa
from src.backend.resolutores.raices.validacion_regla_falsa import validar_entrada_regla_falsa
from src.frontend.controladores.captura_real import entero_capturado, real_capturado

_CLAVES_RESULTADO = {
    "metodo", "entrada", "estado", "mensaje", "codigo_diagnostico", "motivo_parada",
    "aproximacion", "residuo", "intervalo_final", "iteraciones", "iteraciones_totales",
    "advertencias", "informe_continuidad", "contexto_fallo",
}


def _datos():
    return {"expresion": "x^2-2", "extremo_izquierdo": 1, "extremo_derecho": 2,
            "tolerancia": 1e-6, "limite_iteraciones": 100}


@pytest.mark.parametrize("cambios,esperado", [
    ({}, ("EXITO", "TOLERANCIA_RESIDUO", 9)),
    ({"expresion": "x-1"}, ("EXITO", "RAIZ_EN_EXTREMO", 0)),
    ({"expresion": "x", "extremo_izquierdo": 0}, ("EXITO", "RAIZ_EN_EXTREMO", 0)),
    ({"expresion": "x^2+1", "extremo_izquierdo": -1, "extremo_derecho": 1},
     ("SIN_CAMBIO_DE_SIGNO", "SIN_CAMBIO_DE_SIGNO", 0)),
    ({"expresion": "sqrt(x)", "extremo_izquierdo": -1, "extremo_derecho": 1},
     ("ERROR", "DOMINIO_INVALIDO", 0)),
    ({"limite_iteraciones": 1}, ("LIMITE_ITERACIONES", "LIMITE_ITERACIONES", 1)),
    ({"extremo_izquierdo": math.nextafter(math.sqrt(2), -math.inf),
      "extremo_derecho": math.sqrt(2), "tolerancia": 1e-30},
     ("ESTANCAMIENTO", "ESTANCAMIENTO_NUMERICO", 1)),
])
def test_motor_integrado_ofrece_sobre_finito_para_presentacion(cambios, esperado):
    """Comprueba estados reales, filas y serialización sin mocks del cálculo."""
    resultado = regla_falsa(validar_entrada_regla_falsa(_datos() | cambios))
    assert (resultado.estado, resultado.codigo_diagnostico, resultado.iteraciones_totales) == esperado
    sobre = asdict(resultado)
    assert set(sobre) == _CLAVES_RESULTADO
    assert resultado.metodo == "regla_falsa"
    assert resultado.iteraciones_totales == len(resultado.iteraciones)
    json.dumps(sobre, allow_nan=False)
    if resultado.iteraciones:
        ultima = resultado.iteraciones[-1]
        assert resultado.aproximacion == ultima.aproximacion
        assert resultado.residuo == ultima.residuo
        assert resultado.intervalo_final == ultima.intervalo_siguiente


def test_conversion_compartida_alimenta_la_entrada_canonica_real():
    """El motor consume números convertidos, conserva el aviso y devuelve nueve filas."""
    datos = _datos() | {
        "extremo_izquierdo": real_capturado("2", "El extremo a"),
        "extremo_derecho": real_capturado("1", "El extremo b"),
        "tolerancia": real_capturado("1e-6", "La tolerancia"),
        "limite_iteraciones": entero_capturado("100", "El límite"),
    }
    entrada = validar_entrada_regla_falsa(datos)
    resultado = regla_falsa(entrada)
    assert (entrada.extremo_izquierdo, entrada.extremo_derecho) == (1, 2)
    assert entrada.intervalo_invertido and resultado.advertencias == entrada.advertencias
    assert resultado.aproximacion == pytest.approx(1.4142134998513232)
    assert resultado.residuo < entrada.tolerancia and resultado.iteraciones_totales == 9
