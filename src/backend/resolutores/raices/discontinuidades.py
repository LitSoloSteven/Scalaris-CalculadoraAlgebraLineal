"""Diagnóstico conservador de crecimiento bilateral durante la contracción del intervalo."""
import math
from dataclasses import replace
from fractions import Fraction

from .contrato_biseccion import (
    CODIGO_DISCONTINUIDAD, ESTADO_DISCONTINUIDAD, EvidenciaDiscontinuidad,
    IteracionBiseccion, ResultadoBiseccion,
)

_FILAS_CONTRACCION = 6
_FILAS_RESIDUO = 3
_FACTOR_CONTRACCION = 16
_FACTOR_ESCALA_INICIAL = 8
_FACTOR_CRECIMIENTO_LOCAL = 4
_AVISO_SOSPECHA = "La traza sugiere una discontinuidad. Las magnitudes crecieron al reducir el intervalo. Revisa la función y el intervalo."


def calificar_discontinuidad(resultado: ResultadoBiseccion) -> ResultadoBiseccion:
    """Adjunta sospecha sustentada por la traza sin reevaluar ni cambiar el motivo de parada."""
    if resultado.motivo_parada == "raiz_exacta":
        return resultado
    fallo = resultado.estado == "ERROR"
    if fallo and (resultado.contexto_fallo or {}).get("etapa") != "iteracion":
        return resultado
    evidencia = _evidencia(resultado.iteraciones)
    if evidencia is None:
        return resultado
    avisos = resultado.advertencias + (_AVISO_SOSPECHA,)
    if fallo:
        anterior = resultado.diagnostico or {"codigo": resultado.codigo_diagnostico, "origen": "iteracion",
                                            "mensaje": resultado.mensaje}
        diagnostico = {**anterior, "evidencia_discontinuidad": evidencia}
        return replace(resultado, diagnostico=diagnostico, advertencias=avisos)
    return replace(resultado, estado=ESTADO_DISCONTINUIDAD, codigo_diagnostico=CODIGO_DISCONTINUIDAD,
                   mensaje=_AVISO_SOSPECHA, advertencias=avisos,
                   diagnostico={"codigo": CODIGO_DISCONTINUIDAD, "origen": "traza",
                                "mensaje": _AVISO_SOSPECHA, "evidencia_discontinuidad": evidencia,
                                "mensaje_parada": resultado.mensaje})


def _evidencia(filas: tuple[IteracionBiseccion, ...]) -> EvidenciaDiscontinuidad | None:
    if len(filas) < _FILAS_CONTRACCION:
        return None
    ventana = filas[-_FILAS_CONTRACCION:]
    referencia, final = ventana[0], ventana[-1]
    if not all(_encierro_sin_cero(fila) for fila in ventana):
        return None
    if Fraction(final.ancho) * _FACTOR_CONTRACCION > referencia.ancho:
        return None
    inicial = filas[0]
    escala = max(abs(inicial.f_a), abs(inicial.f_b))
    vecinal = _magnitud_vecinal(referencia)
    magnitud_final = _magnitud_vecinal(final)
    residuo = min(fila.residuo for fila in ventana[-_FILAS_RESIDUO:])
    evidencia_minima = Fraction(min(magnitud_final, residuo))
    if evidencia_minima < Fraction(escala) * _FACTOR_ESCALA_INICIAL:
        return None
    if evidencia_minima < Fraction(vecinal) * _FACTOR_CRECIMIENTO_LOCAL:
        return None
    return {"intervalo": (final.extremo_izquierdo, final.extremo_derecho),
            "ancho_referencia": referencia.ancho, "escala_inicial": escala,
            "magnitud_vecinal_referencia": vecinal, "magnitud_vecinal_final": magnitud_final,
            "residuo_reciente_minimo": residuo}


def _encierro_sin_cero(fila: IteracionBiseccion) -> bool:
    return (fila.ancho > 0 and 0 not in (fila.f_a, fila.f_b, fila.f_c)
            and math.copysign(1, fila.f_a) != math.copysign(1, fila.f_b))


def _magnitud_vecinal(fila: IteracionBiseccion) -> float:
    return min(abs(fila.f_a), abs(fila.f_b))
