"""Recortes conservadores del dominio y preservación del resultado original."""
from copy import deepcopy
from dataclasses import replace

import pytest

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.regla_falsa import regla_falsa
from src.backend.resolutores.raices.sugerencias_regla_falsa import sugerir_acciones_regla_falsa


@pytest.mark.parametrize("expresion,esperado", [("sqrt(x)-1", (0, 4)),
    ("1/(x-0.1234)", None), ("sqrt(x)/(x-0.1234)", None), ("x^2+1", None)])
def test_sugerencia_estructural_no_atraviesa_polos_ni_muta_resultados(expresion, esperado):
    """Propone solo recortes seguros y conserva idéntico el resultado de origen."""
    entrada = EntradaReglaFalsa(expresion=expresion, extremo_izquierdo=-1, extremo_derecho=4)
    resultado = regla_falsa(entrada)
    original = deepcopy(resultado)
    propuestas = sugerir_acciones_regla_falsa(entrada, resultado)
    assert resultado == original
    if esperado is None:
        assert propuestas == ()
    else:
        assert propuestas[0]["intervalo"] == esperado
        assert "no certifica" in propuestas[0]["mensaje"]


def test_rechazar_resultado_ajeno_y_contratos_invalidos():
    """Rechaza resultados de otra entrada y objetos ajenos al contrato de regla falsa."""
    entrada = EntradaReglaFalsa(expresion="sqrt(x)-1", extremo_izquierdo=-1, extremo_derecho=4)
    with pytest.raises(ValueError):
        sugerir_acciones_regla_falsa(replace(entrada, expresion="x"), regla_falsa(entrada))
    with pytest.raises(ValueError):
        sugerir_acciones_regla_falsa({}, {})
