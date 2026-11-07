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
    return EntradaReglaFalsa(expresion, a, b, tol, limite)


def test_oraculo_excel_potencia_decima_converge():
    """x^10 - 1 en [0, 1.3] debe converger con tolerancia 1e-6."""
    resultado = regla_falsa(_entrada("x^10 - 1", 0.0, 1.3))
    assert resultado.estado == "EXITO", (
        f"esperaba EXITO, obtuvo {resultado.estado} "
        f"(motivo={resultado.motivo_parada}, residuo={resultado.metricas.get('residuo_final')})"
    )
    assert resultado.aproximacion is not None
    assert abs(resultado.aproximacion - 1.0) < 1e-4
    assert resultado.metricas["iteraciones_totales"] >= 1
    # El cierre debe ser por residuo o por cero evaluado, nunca por límite.
    assert resultado.motivo_parada in {"tolerancia_residuo", "secante_exacta", "raiz_en_extremo"}


def test_oraculo_excel_polinomio_converge():
    """x^4 - 5x^3 + 0.5x^2 - 11x + 10 en [0.6, 1] debe converger con tolerancia 1e-6."""
    resultado = regla_falsa(_entrada("x^4 - 5*x^3 + 0.5*x^2 - 11*x + 10", 0.6, 1.0))
    assert resultado.estado == "EXITO", (
        f"esperaba EXITO, obtuvo {resultado.estado} "
        f"(motivo={resultado.motivo_parada}, residuo={resultado.metricas.get('residuo_final')})"
    )
    assert resultado.aproximacion is not None
    assert resultado.motivo_parada in {"tolerancia_residuo", "secante_exacta", "raiz_en_extremo"}


def test_resultado_es_serializable_con_json_estricto():
    """asdict + json.dumps(allow_nan=False) debe aceptar el resultado sin NaN ni infinitos."""
    resultado = regla_falsa(_entrada("x^2 - 2", 1.0, 2.0))
    datos = asdict(resultado)
    texto = json.dumps(datos, allow_nan=False)  # lanza si hay NaN/Inf
    assert isinstance(texto, str) and texto
    # Claves obligatorias del contrato.
    for clave in (
        "estado",
        "mensaje",
        "aproximacion",
        "intervalo_final",
        "tolerancia",
        "iteraciones",
        "motivo_parada",
        "metricas",
        "codigo_diagnostico",
        "advertencias",
        "diagnostico",
        "contexto_fallo",
        "unidad_angular",
        "informe_continuidad",
    ):
        assert clave in datos, f"falta la clave {clave}"
    # Cada iteración también debe ser serializable.
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
    # Revalidar los campos canónicos (sin revalidar el aviso de inversión ya aplicado).
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
        intervalo_invertido=False,   # el dict canónico no reaplica la inversión
        unidad_angular=original.unidad_angular,
    )