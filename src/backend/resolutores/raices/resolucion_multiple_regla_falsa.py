"""Resolución de candidatos por falsa posición con reserva previa y fallos aislados."""
from dataclasses import replace

from .contrato_exploracion import CandidatoExploracion
from .contrato_lote_regla_falsa import (
    EntradaLoteReglaFalsa, ResolucionCandidatoReglaFalsa, ResultadoLoteReglaFalsa,
    validar_lote_regla_falsa,
)
from .contrato_regla_falsa_ampliada import ConfiguracionReglaFalsa
from .contrato_resolucion_multiple import CandidatoResolucion
from .regla_falsa_ampliada import resolver_regla_falsa_configurada
from .validacion_raices import validar_extremo

EVALUACIONES_EXTREMOS_REGLA_FALSA = 2


def resolver_candidatos_regla_falsa(entrada: EntradaLoteReglaFalsa) -> ResultadoLoteReglaFalsa:
    """Resuelve en orden sin bisección; lanza ValueError solo por un contrato global inválido."""
    entrada = validar_lote_regla_falsa(entrada)
    reserva = entrada.configuracion.entrada.limite_iteraciones + EVALUACIONES_EXTREMOS_REGLA_FALSA
    resultados: list[ResolucionCandidatoReglaFalsa] = []
    reservadas = 0
    for candidato in entrada.candidatos:
        if reservadas + reserva > entrada.presupuesto_evaluaciones:
            resultados.append(ResolucionCandidatoReglaFalsa(
                candidato.identificador, "PRESUPUESTO_AGOTADO",
                "No se ejecutó este candidato: no cabe en el presupuesto restante. Resuélvelo individualmente.",
            ))
            continue
        reservadas += reserva
        registro = _resolver_candidato(entrada.configuracion, candidato)
        resultados.append(replace(registro, evaluaciones_reservadas=reserva))
    filas = sum(len(registro.respuesta.resultado.iteraciones)
                for registro in resultados if registro.respuesta is not None)
    return ResultadoLoteReglaFalsa(
        tuple(resultados), reservadas, filas,
        any(registro.estado == "PRESUPUESTO_AGOTADO" for registro in resultados),
    )


def _resolver_candidato(
    configuracion: ConfiguracionReglaFalsa, registro: CandidatoResolucion,
) -> ResolucionCandidatoReglaFalsa:
    try:
        configurada = _configurar_candidato(configuracion, registro.candidato)
        respuesta = resolver_regla_falsa_configurada(configurada)
    except ValueError:
        return ResolucionCandidatoReglaFalsa(
            registro.identificador, "NO_APTO",
            "El candidato no es apto para la función actual. Vuelve a explorar y selecciona un cruce o cero válido.",
        )
    except Exception:
        return ResolucionCandidatoReglaFalsa(
            registro.identificador, "ERROR",
            "No se pudo resolver este candidato. Revisa la captura e inténtalo de nuevo.",
        )
    resultado = respuesta.resultado
    return ResolucionCandidatoReglaFalsa(
        registro.identificador, resultado.estado, resultado.mensaje,
        respuesta, informe_continuidad=resultado.informe_continuidad,
    )


def _configurar_candidato(
    configuracion: ConfiguracionReglaFalsa, candidato: CandidatoExploracion,
) -> ConfiguracionReglaFalsa:
    if not isinstance(candidato, CandidatoExploracion) or candidato.tipo not in ("cruce", "cero_evaluado"):
        raise ValueError("Selecciona un cruce o cero evaluado.")
    intervalo = candidato.intervalo
    if not isinstance(intervalo, tuple) or len(intervalo) != 2:
        raise ValueError("El candidato requiere dos extremos.")
    inferior = validar_extremo(intervalo[0], "a")
    superior = validar_extremo(intervalo[1], "b")
    if inferior >= superior:
        raise ValueError("El intervalo del candidato debe cumplir a < b.")
    cero = None
    if candidato.tipo == "cero_evaluado":
        cero = validar_extremo(candidato.abscisa, "cero elegido")
        if cero not in (inferior, superior):
            raise ValueError("El cero elegido debe pertenecer a un extremo del candidato.")
    entrada = replace(configuracion.entrada, extremo_izquierdo=inferior,
                      extremo_derecho=superior, intervalo_invertido=False)
    return ConfiguracionReglaFalsa(entrada, configuracion.criterio, cero)
