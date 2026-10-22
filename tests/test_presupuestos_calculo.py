"""Rechazo temprano de trabajo excesivo sin alterar resultados admitidos."""
from fractions import Fraction
from unittest.mock import Mock

import pytest

from src.backend.constantes import (
    LONGITUD_MAXIMA_ENTRADA_BASES,
    LONGITUD_MAXIMA_EXPRESION_MATRICIAL,
    MAXIMO_OPERACIONES_EXPRESION_MATRICIAL,
)
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import EvaluadorExpresionesMatriciales
from src.backend.resolutores.operaciones_matrices.presupuesto_expresiones import validar_presupuesto_operaciones
from src.backend.resolutores.sistemas_numericos.conversor_bases import ConversorBases
from src.backend.utilidades.reglas_dominio import capturar_entrada_base, validar_entrada_base


def test_expresion_larga_se_rechaza_antes_de_tokenizar(monkeypatch):
    """El presupuesto de caracteres precede cualquier procesamiento léxico."""
    evaluador = EvaluadorExpresionesMatriciales()
    tokenizar = Mock(side_effect=AssertionError("No debe analizar una entrada excesiva"))
    monkeypatch.setattr(evaluador, "_tokenizar", tokenizar)
    respuesta = evaluador.evaluar("A" * (LONGITUD_MAXIMA_EXPRESION_MATRICIAL + 1), {})
    assert respuesta["estado"] == "ERROR"
    assert "caracteres" in respuesta["mensaje"]
    assert respuesta["pasos_segmento"] == []
    tokenizar.assert_not_called()


@pytest.mark.parametrize("operador", ["+", "*", "ᵀ", "-"])
def test_operaciones_excesivas_se_rechazan_sin_calcular(monkeypatch, operador):
    """Cada familia de operador tiene presupuesto previo al recorrido de evaluación."""
    evaluador = EvaluadorExpresionesMatriciales()
    consumir = Mock(side_effect=AssertionError("No debe ejecutar operaciones excesivas"))
    monkeypatch.setattr(evaluador, "_consumir_token_rpn", consumir)
    expresion = operador.join(["A"] * (MAXIMO_OPERACIONES_EXPRESION_MATRICIAL + 2))
    respuesta = evaluador.evaluar(expresion, {"A": Matriz(1, 1, [[1]])})
    assert respuesta["estado"] == "ERROR"
    assert "operaciones" in respuesta["mensaje"]
    assert respuesta["pasos_segmento"] == []
    consumir.assert_not_called()


def test_limite_de_operaciones_conserva_fraccion_exacta():
    """El límite inclusive conserva aritmética y todos los pasos de suma."""
    cantidad = MAXIMO_OPERACIONES_EXPRESION_MATRICIAL
    respuesta = EvaluadorExpresionesMatriciales().evaluar(
        "+".join(["A"] * (cantidad + 1)), {"A": Matriz(1, 1, [[Fraction(1001, 1000)]])}
    )
    assert respuesta["estado"] == "EXITO"
    assert respuesta["matriz_resultado"].datos == [[Fraction(1001 * (cantidad + 1), 1000)]]
    assert len(respuesta["pasos_segmento"]) == cantidad


def test_presupuesto_considera_dimensiones_reales_y_solo_matrices_usadas():
    """Las cargas directas grandes no eluden la cota de instantáneas."""
    matrices = {"A": Matriz(30, 30), "B": Matriz(1, 1, [[1]])}
    with pytest.raises(ValueError, match="dimensiones"):
        validar_presupuesto_operaciones(["A", "*", "A"], matrices)
    validar_presupuesto_operaciones(["B", "+", "B"], matrices)


@pytest.mark.parametrize("base", [2, 8, 10, 16])
def test_bases_rechaza_ceros_excesivos_antes_de_convertir(monkeypatch, base):
    """Ni los ceros ni separadores eluden la validación compartida de captura."""
    convertir = Mock(side_effect=AssertionError("No debe calcular una magnitud excesiva"))
    monkeypatch.setattr("src.backend.utilidades.reglas_dominio._capturar_magnitud_base", convertir)
    texto = "0" * (LONGITUD_MAXIMA_ENTRADA_BASES + 1)
    with pytest.raises(ValueError, match="caracteres"):
        capturar_entrada_base(texto, base)
    assert validar_entrada_base(texto, base)[0] is False
    convertir.assert_not_called()


@pytest.mark.parametrize("longitud", [800, LONGITUD_MAXIMA_ENTRADA_BASES])
def test_bases_admite_limite_inclusive_y_conserva_expansion(longitud):
    """El caso histórico de 800 bits y la frontera mantienen sus potencias exactas."""
    respuesta = ConversorBases().binario_a_todo("0" * longitud, "decimal")
    assert respuesta["estado"] == "EXITO"
    assert respuesta["decimal"] == "0"
    terminos = respuesta["pasos"][0]["terminos"]
    assert len(terminos) == longitud
    assert terminos[0]["peso"] == 2 ** (longitud - 1)
    assert terminos[-1]["peso"] == 1


def test_conversor_publico_devuelve_error_granular_por_presupuesto():
    """El conversor comunica el límite sin calcular pasos ni truncar el número."""
    respuesta = ConversorBases().hexadecimal_a_todo("0" * (LONGITUD_MAXIMA_ENTRADA_BASES + 1))
    assert respuesta["estado"] == "ERROR"
    assert "caracteres" in respuesta["mensaje"]
    assert "pasos" not in respuesta
