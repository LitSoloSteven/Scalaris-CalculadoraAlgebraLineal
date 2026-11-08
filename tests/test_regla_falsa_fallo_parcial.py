"""Pruebas de fallo a mitad del recorrido en regla falsa."""
import importlib
import math

import pytest

from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa


def test_fallo_tras_filas_validas_conserva_traza_e_intervalo(monkeypatch):
    """Un fallo en la tercera evaluación conserva las dos filas válidas y el último intervalo."""
    modulo = importlib.import_module("src.backend.resolutores.raices.regla_falsa")
    original = modulo.evaluar
    llamadas = {"n": 0}

    def evaluar_con_fallo(funcion, valor):
        """Delega en la evaluacion real salvo en la tercera llamada, que simula un fallo de dominio."""
        llamadas["n"] += 1
        if llamadas["n"] == 3:
            raise ErrorDominio("fuera de dominio", "DOMINIO_INVALIDO")
        return original(funcion, valor)

    monkeypatch.setattr(modulo, "evaluar", evaluar_con_fallo)
    resultado = modulo.regla_falsa(
        EntradaReglaFalsa(
            expresion="x^2-2", extremo_izquierdo=1, extremo_derecho=2
        )
    )

    assert resultado.estado == "ERROR"
    assert resultado.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert resultado.iteraciones_totales == 2
    assert len(resultado.iteraciones) == 2
    assert all(
        math.isfinite(fila.aproximacion) and math.isfinite(fila.valor_aproximacion)
        for fila in resultado.iteraciones
    )
    assert resultado.aproximacion is None
    assert resultado.residuo is None
    assert resultado.intervalo_final == pytest.approx((1.4, 2.0))
    assert resultado.intervalo_final == resultado.contexto_fallo["intervalo_valido"]
    assert resultado.contexto_fallo["etapa"] == "iteracion"
    assert resultado.contexto_fallo["x_fallo"] == pytest.approx(1.4117647, rel=1e-6)