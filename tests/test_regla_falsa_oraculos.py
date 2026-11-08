"""Oráculos del Excel, serialización y reconstrucción del contrato de regla falsa."""
import json
from dataclasses import asdict

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import (
    EntradaReglaFalsa,
    IteracionReglaFalsa,
    ResultadoReglaFalsa,
)
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from src.backend.resolutores.raices.validacion_regla_falsa import validar_entrada_regla_falsa


def _entrada(expresion, a, b, tol=1e-6, limite=100):
    return EntradaReglaFalsa(
        expresion=expresion,
        extremo_izquierdo=a,
        extremo_derecho=b,
        tolerancia=tol,
        limite_iteraciones=limite,
    )


def test_oraculo_excel_potencia_decima_converge():
    """x^10 - 1 en [0, 1.3] debe converger con tolerancia 1e-6."""
    resultado = regla_falsa(_entrada("x^10 - 1", 0.0, 1.3))
    assert resultado.estado == "EXITO", (
        f"esperaba EXITO, obtuvo {resultado.estado} "
        f"(motivo={resultado.motivo_parada}, residuo={resultado.residuo})"
    )
    assert resultado.aproximacion is not None
    assert abs(resultado.aproximacion - 1.0) < 1e-4
    assert resultado.iteraciones_totales >= 1
    assert resultado.motivo_parada in {"tolerancia_residuo", "raiz_en_aproximacion", "raiz_en_extremo"}


def test_oraculo_excel_polinomio_converge():
    """x^4 - 5x^3 + 0.5x^2 - 11x + 10 en [0.6, 1] debe converger con tolerancia 1e-6."""
    resultado = regla_falsa(_entrada("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", 0.6, 1.0))
    assert resultado.estado == "EXITO", (
        f"esperaba EXITO, obtuvo {resultado.estado} "
        f"(motivo={resultado.motivo_parada}, residuo={resultado.residuo})"
    )
    assert resultado.aproximacion is not None
    assert resultado.motivo_parada in {"tolerancia_residuo", "raiz_en_aproximacion", "raiz_en_extremo"}


def test_resultado_es_serializable_con_json_estricto():
    """asdict + json.dumps(allow_nan=False) debe aceptar el resultado sin NaN ni infinitos."""
    resultado = regla_falsa(_entrada("x^2 - 2", 1.0, 2.0))
    datos = asdict(resultado)
    texto = json.dumps(datos, allow_nan=False)
    assert isinstance(texto, str) and texto
    for clave in (
        "metodo",
        "entrada",
        "estado",
        "mensaje",
        "codigo_diagnostico",
        "motivo_parada",
        "aproximacion",
        "residuo",
        "intervalo_final",
        "iteraciones",
        "iteraciones_totales",
        "advertencias",
        "informe_continuidad",
        "contexto_fallo",
    ):
        assert clave in datos, f"falta la clave {clave}"
    for fila in datos["iteraciones"]:
        assert isinstance(fila, dict)
        json.dumps(fila, allow_nan=False)


def test_entrada_regla_falsa_se_reconstruye_desde_dict():
    """El dict canónico se revalida a la misma dataclass (ida y vuelta)."""
    original = EntradaReglaFalsa(
        expresion="x^3 - 2",
        extremo_izquierdo=1.0,
        extremo_derecho=2.0,
        tolerancia=1e-5,
        limite_iteraciones=50,
        intervalo_invertido=True,
        unidad_angular="grados",
    )
    reconstruida = validar_entrada_regla_falsa({
        "expresion": original.expresion,
        "extremo_izquierdo": original.extremo_izquierdo,
        "extremo_derecho": original.extremo_derecho,
        "tolerancia": original.tolerancia,
        "limite_iteraciones": original.limite_iteraciones,
        "unidad_angular": original.unidad_angular,
    })
    assert reconstruida == EntradaReglaFalsa(
        expresion=original.expresion,
        extremo_izquierdo=original.extremo_izquierdo,
        extremo_derecho=original.extremo_derecho,
        tolerancia=original.tolerancia,
        limite_iteraciones=original.limite_iteraciones,
        intervalo_invertido=False,
        unidad_angular=original.unidad_angular,
    )