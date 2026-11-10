"""Ejecución configurada sobre el mismo motor de secantes del contrato clásico."""
import math
from dataclasses import asdict, replace

from .contrato_regla_falsa import EntradaReglaFalsa
from .contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa, ResultadoReglaFalsaAmpliado
from .criterios_regla_falsa import MOTIVOS_CRITERIO, metrica_regla_falsa, validar_criterio_regla_falsa
from .preparacion_regla_falsa import IntervaloReglaFalsaPreparado, preparar_intervalo_regla_falsa
from .regla_falsa import resolver_intervalo_regla_falsa
from .validacion_regla_falsa import validar_entrada_regla_falsa


def resolver_regla_falsa_configurada(configuracion: ConfiguracionReglaFalsa) -> ResultadoReglaFalsaAmpliado:
    """Resuelve con un solo criterio; lanza ValueError por configuración o cero inválidos."""
    if not isinstance(configuracion, ConfiguracionReglaFalsa) or not isinstance(configuracion.entrada, EntradaReglaFalsa):
        raise ValueError("La configuración debe cumplir el contrato ampliado de regla falsa.")
    entrada = validar_entrada_regla_falsa(asdict(configuracion.entrada))
    criterio = validar_criterio_regla_falsa(configuracion.criterio, entrada.limite_iteraciones)
    preparado = preparar_intervalo_regla_falsa(entrada)
    cero = _validar_cero(configuracion.cero_preferido, preparado)
    resultado = resolver_intervalo_regla_falsa(preparado, criterio, cero)
    metrica = metrica_regla_falsa(criterio, resultado.iteraciones[-1]) if resultado.iteraciones else None
    cumplimiento = "NO_APLICA" if metrica is None else "NO_CUMPLIDO"
    if resultado.motivo_parada == MOTIVOS_CRITERIO[criterio.tipo]:
        cumplimiento = "CONTEO_COMPLETADO" if criterio.tipo == "iteraciones" else "CUMPLIDO"
    if resultado.codigo_diagnostico == "LIMITE_ITERACIONES":
        resultado = replace(resultado, mensaje="Se alcanzo el limite global sin cumplir el criterio solicitado.")
    umbral = criterio.parametro if criterio.tipo == "iteraciones" else float(criterio.umbral)
    return ResultadoReglaFalsaAmpliado(resultado, criterio, cumplimiento, metrica, umbral)


def _validar_cero(valor: object, preparado: IntervaloReglaFalsaPreparado) -> float | None:
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("El cero elegido debe ser un extremo real y finito.")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ValueError("El cero elegido excede la capacidad numérica.") from error
    if not math.isfinite(numero) or numero not in preparado.intervalo:
        raise ValueError("El cero elegido debe pertenecer a los extremos actuales.")
    if not _es_cero_admisible(numero, preparado):
        raise ValueError("El extremo elegido ya no se evalúa como cero.")
    return numero


def _es_cero_admisible(numero: float, preparado: IntervaloReglaFalsaPreparado) -> bool:
    return preparado.admite_cero and any(
        evaluacion["abscisa"] == numero and evaluacion["valor"] == 0
        for evaluacion in preparado.evaluaciones
    )
