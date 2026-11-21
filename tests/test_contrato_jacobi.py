"""Comprobaciones de la traza y los diagnósticos del contrato de Jacobi."""
from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.jacobi.contrato_jacobi import (
    DiagnosticoJacobi,
    PasoJacobi,
    ResultadoJacobi,
)


def test_el_total_se_deriva_de_la_traza_inmutable() -> None:
    """El resultado cuenta el paso completo y conserva sus fracciones al consultarlo."""
    paso = PasoJacobi(
        indice=1,
        vector_anterior=(Fraction(0),),
        vector_nuevo=(Fraction(1, 3),),
        norma_cambio=Fraction(1, 3),
        norma_residuo=Fraction(0),
    )
    resultado = ResultadoJacobi(
        codigo="SOLUCION_EXACTA",
        aproximacion=paso.vector_nuevo,
        residuo=(Fraction(0),),
        norma_residuo=paso.norma_residuo,
        dominancia_estricta=True,
        pasos=(paso,),
    )

    assert resultado.iteraciones_realizadas == 1
    assert resultado.pasos[0].vector_nuevo == (Fraction(1, 3),)
    with pytest.raises(FrozenInstanceError):
        setattr(paso, "indice", 2)
    with pytest.raises(FrozenInstanceError):
        setattr(resultado, "pasos", ())


def test_el_diagnostico_sin_traza_conserva_su_ubicacion() -> None:
    """Una diagonal nula puede señalar una celda sin registrar iteraciones."""
    diagnostico = DiagnosticoJacobi(
        mensaje="El coeficiente diagonal debe ser distinto de cero.",
        campo="matriz_a",
        fila=1,
        columna=1,
    )
    resultado = ResultadoJacobi(codigo="DIAGONAL_NULA", diagnostico=diagnostico)

    assert resultado.iteraciones_realizadas == 0
    assert resultado.aproximacion is None
    assert resultado.diagnostico is diagnostico
