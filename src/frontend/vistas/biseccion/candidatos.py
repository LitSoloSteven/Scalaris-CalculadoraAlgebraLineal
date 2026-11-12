"""Presentación compatible de candidatos para el panel de bisección."""
from src.frontend.componentes.candidatos_raices import (
    PresentacionCandidatos, mostrar_candidatos as mostrar_candidatos_raices,
)

_PRESENTACION = PresentacionCandidatos(
    "Bisección obtiene como máximo una aproximación por cálculo. Carga un intervalo y después pide calcular.",
    "biseccion-numero",
)


def mostrar_candidatos(panel, respuesta: dict) -> None:
    """Entrega la respuesta y la acción vigente al componente independiente."""
    mostrar_candidatos_raices(respuesta, panel.seleccionar, _PRESENTACION)
