"""Construccion de trazas y cierres de regla falsa."""
from collections.abc import Sequence
from dataclasses import replace

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from .aritmetica_biseccion import ancho_intervalo
from .aritmetica_regla_falsa import error_relativo_numerico
from .contrato_regla_falsa import EntradaReglaFalsa, IteracionReglaFalsa, ResultadoReglaFalsa
from .decision_biseccion import signo_producto
from .traza_comun_raices import registrar_accion, texto_error_relativo

_CIERRES = {
    "secante_exacta": (
        "EXITO", "CERO_EVALUADO",
        "La aproximacion de la secante se evaluo como cero; esto no certifica exactitud simbolica.",
    ),
    "tolerancia_residuo": (
        "EXITO", "CONVERGENCIA_POR_RESIDUO",
        "El residuo es menor que la tolerancia solicitada; no es una cota del error en x.",
    ),
    "raiz_en_extremo": (
        "EXITO", "CERO_EVALUADO",
        "La funcion se evaluo como cero en un extremo; esto no certifica exactitud simbolica.",
    ),
    "sin_cambio_signo": (
        "SIN_CAMBIO_DE_SIGNO", "SIN_CAMBIO_DE_SIGNO",
        "Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
    ),
    "limite_iteraciones": (
        "LIMITE_ITERACIONES", "LIMITE_ITERACIONES",
        "Se alcanzo el limite de iteraciones sin cumplir la tolerancia solicitada.",
    ),
    "estancamiento": (
        "ESTANCAMIENTO", "ESTANCAMIENTO",
        "La aproximacion de la secante coincide con un extremo. La representacion numerica no permite reducir el intervalo.",
    ),
}


def crear_iteracion(
    indice: int,
    extremos: tuple[float, float, float, float],
    medio: tuple[float, float],
    previo: float | None,
) -> IteracionReglaFalsa:
    """Construye una fila con metricas finitas y error relativo numerico."""
    inferior, superior, valor_inferior, valor_superior = extremos
    cruce, valor_cruce = medio
    relativo = error_relativo_numerico(cruce, previo)
    texto = texto_error_relativo(cruce, previo, relativo)
    return IteracionReglaFalsa(
        i=indice,
        extremo_izquierdo=inferior,
        extremo_derecho=superior,
        c=cruce,
        f_a=valor_inferior,
        f_b=valor_superior,
        f_c=valor_cruce,
        ancho=ancho_intervalo(inferior, superior),
        residuo=abs(valor_cruce),
        error_relativo=texto,
        error_relativo_valor=relativo,
        signo_producto=signo_producto(valor_inferior, valor_cruce),
        explicacion="",
    )

def construir_resultado(
    entrada: EntradaReglaFalsa,
    intervalo: tuple[float, float],
    iteraciones: Sequence[IteracionReglaFalsa],
    motivo: str,
    muestra: tuple[float, float],
) -> ResultadoReglaFalsa:
    """Devuelve un cierre coherente con la ultima muestra, sin reevaluar."""
    estado, codigo, mensaje = _CIERRES[motivo]
    return ResultadoReglaFalsa(
        estado=estado,
        mensaje=mensaje,
        aproximacion=muestra[0],
        intervalo_final=intervalo,
        tolerancia=entrada.tolerancia,
        iteraciones=tuple(iteraciones),
        motivo_parada=motivo,
        codigo_diagnostico=codigo,
        metricas={"iteraciones_totales": len(iteraciones), "residuo_final": abs(muestra[1])},
        unidad_angular=entrada.unidad_angular,
    )


def construir_error(
    error: ValueError,
    iteraciones: Sequence[IteracionReglaFalsa] = (),
    codigo: str = "EXPRESION_INVALIDA",
) -> ResultadoReglaFalsa:
    """Conserva la traza valida y clasifica el error sin publicar aproximaciones."""
    if isinstance(error, ErrorNoFinito):
        codigo = "EVALUACION_NO_FINITA"
    elif isinstance(error, ErrorDominio):
        codigo = "DOMINIO_INVALIDO"
    return ResultadoReglaFalsa(
        estado="ERROR",
        mensaje=str(error),
        iteraciones=tuple(iteraciones),
        motivo_parada="evaluacion_invalida",
        codigo_diagnostico=getattr(error, "codigo", codigo),
        metricas={"iteraciones_totales": len(iteraciones)},
    )