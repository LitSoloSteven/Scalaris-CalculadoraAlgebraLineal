"""Conversión de campos de regla falsa al contrato real del dominio."""
from collections.abc import Mapping

from src.backend.resolutores.raices.contrato_regla_falsa import EntradaReglaFalsa
from src.backend.resolutores.raices.validacion_regla_falsa import validar_entrada_regla_falsa
from src.frontend.controladores.captura_real import entero_capturado, real_capturado


def preparar_entrada(captura: Mapping[str, object]) -> EntradaReglaFalsa:
    """Convierte la captura y devuelve la entrada canónica; propaga ValueError orientativo."""
    if not isinstance(captura, Mapping):
        raise ValueError("Introduce la expresión y los extremos del intervalo.")
    datos = {
        "expresion": captura.get("expresion", ""),
        "extremo_izquierdo": real_capturado(captura.get("extremo_izquierdo"), "El extremo a"),
        "extremo_derecho": real_capturado(captura.get("extremo_derecho"), "El extremo b"),
    }
    if "tolerancia" in captura:
        datos["tolerancia"] = real_capturado(captura["tolerancia"], "La tolerancia de residuo")
    if "limite_iteraciones" in captura:
        datos["limite_iteraciones"] = entero_capturado(captura["limite_iteraciones"], "El límite")
    for campo in ("unidad_angular", "intervalo_invertido"):
        if campo in captura:
            datos[campo] = captura[campo]
    return validar_entrada_regla_falsa(datos)
