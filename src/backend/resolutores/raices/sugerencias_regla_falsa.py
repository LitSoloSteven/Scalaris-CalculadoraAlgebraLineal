"""Propuestas conservadoras de intervalo verificadas para regla falsa."""
from dataclasses import asdict
from typing import Literal, TypedDict

from .contrato_regla_falsa import EntradaReglaFalsa, ResultadoReglaFalsa
from .sugerencias_dominio import sugerir_recorte_dominio
from .validacion_regla_falsa import validar_entrada_regla_falsa


class SugerenciaIntervaloReglaFalsa(TypedDict):
    """Describe un recorte respaldado por restricciones y evaluaciones del dominio."""

    tipo: Literal["intervalo_dominio"]
    intervalo: tuple[float, float]
    mensaje: str


def sugerir_acciones_regla_falsa(
    entrada: EntradaReglaFalsa, resultado: ResultadoReglaFalsa,
) -> tuple[SugerenciaIntervaloReglaFalsa, ...]:
    """Devuelve recortes sin mutar datos; lanza ValueError por contratos incompatibles."""
    if not isinstance(entrada, EntradaReglaFalsa) or not isinstance(resultado, ResultadoReglaFalsa):
        raise ValueError("La sugerencia requiere entrada y resultado de regla falsa.")
    canonica = validar_entrada_regla_falsa(asdict(entrada))
    if resultado.entrada != canonica:
        raise ValueError("El resultado debe corresponder a la entrada actual.")
    if resultado.codigo_diagnostico != "DOMINIO_INVALIDO":
        return ()
    intervalo = sugerir_recorte_dominio(
        canonica.expresion, (canonica.extremo_izquierdo, canonica.extremo_derecho), canonica.unidad_angular)
    if intervalo is None:
        return ()
    return ({"tipo": "intervalo_dominio", "intervalo": intervalo,
             "mensaje": "Puedes cargar un intervalo recortado al dominio de sqrt. Se comprobaron sus extremos "
                        "y restricciones reconocidas; no certifica continuidad ni cambio de signo."},)
