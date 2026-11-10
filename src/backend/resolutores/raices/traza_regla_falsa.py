"""Construccion de trazas y cierres de regla falsa."""
from collections.abc import Sequence
from dataclasses import replace

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from .aritmetica_biseccion import ancho_intervalo
from .aritmetica_regla_falsa import error_relativo_numerico, peso_escalado
from .contrato_regla_falsa import EntradaReglaFalsa, IteracionReglaFalsa, ResultadoReglaFalsa
from .decision_biseccion import signo_producto

_CIERRES = {
    "criterio_ancho_cumplido": (
        "EXITO", "CRITERIO_ANCHO_CUMPLIDO",
        "El ancho del intervalo posterior cumple el umbral; no certifica el error de la secante.",
    ),
    "criterio_decimales_cumplido": (
        "EXITO", "CRITERIO_DECIMALES_CUMPLIDO",
        "El ancho posterior cumple el umbral decimal; no garantiza cifras correctas de la aproximacion.",
    ),
    "criterio_relativo_cumplido": (
        "EXITO", "CRITERIO_RELATIVO_CUMPLIDO",
        "El cambio relativo entre aproximaciones cumple el porcentaje; no certifica exactitud.",
    ),
    "iteraciones_solicitadas_completadas": (
        "EXITO", "ITERACIONES_SOLICITADAS_COMPLETADAS",
        "Se completo el numero de iteraciones solicitado; no se certifica precision alcanzada.",
    ),
    "raiz_en_extremo": (
        "EXITO", "RAIZ_EN_EXTREMO",
        "La funcion se evaluo como cero en un extremo; no se infiere unicidad.",
    ),
    "raiz_en_aproximacion": (
        "EXITO", "RAIZ_EN_APROXIMACION",
        "La aproximacion se evaluo como cero; esto no certifica exactitud simbolica.",
    ),
    "tolerancia_residuo": (
        "EXITO", "TOLERANCIA_RESIDUO",
        "El residuo es menor que la tolerancia solicitada; no es una cota del error en x.",
    ),
    "sin_cambio_de_signo": (
        "SIN_CAMBIO_DE_SIGNO", "SIN_CAMBIO_DE_SIGNO",
        "Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
    ),
    "estancamiento_numerico": (
        "ESTANCAMIENTO", "ESTANCAMIENTO_NUMERICO",
        "La aproximacion de la secante no permite reducir el intervalo.",
    ),
    "limite_iteraciones": (
        "LIMITE_ITERACIONES", "LIMITE_ITERACIONES",
        "Se alcanzo el limite de iteraciones sin cumplir la tolerancia solicitada.",
    ),
}


def crear_iteracion(
    indice: int,
    extremos: tuple[float, float, float, float],
    medio: tuple[float, float],
    previo: float | None,
) -> IteracionReglaFalsa:
    """Construye una fila con metricas finitas, peso e intervalo siguiente."""
    inferior, superior, valor_inferior, valor_superior = extremos
    aproximacion, valor_aproximacion = medio
    relativo = error_relativo_numerico(aproximacion, previo)
    peso = peso_escalado(valor_inferior, valor_superior)
    signo = signo_producto(valor_inferior, valor_aproximacion)

    if valor_aproximacion == 0:
        accion = "raiz"
        intervalo_siguiente = (aproximacion, aproximacion)
    elif signo == -1:
        accion = "reemplazar_b"
        intervalo_siguiente = (inferior, aproximacion)
    else:
        accion = "reemplazar_a"
        intervalo_siguiente = (aproximacion, superior)

    return IteracionReglaFalsa(
        i=indice,
        extremo_izquierdo=inferior,
        extremo_derecho=superior,
        valor_izquierdo=valor_inferior,
        valor_derecho=valor_superior,
        aproximacion=aproximacion,
        valor_aproximacion=valor_aproximacion,
        residuo=abs(valor_aproximacion),
        ancho=ancho_intervalo(inferior, superior),
        peso_secante=peso,
        error_relativo_porcentual=relativo,
        signo_producto=signo,
        accion=accion,
        intervalo_siguiente=intervalo_siguiente,
    )


def crear_iteracion_estancamiento(
    indice: int,
    extremos: tuple[float, float, float, float],
    muestra: tuple[float, float],
    intervalo: tuple[float, float],
) -> IteracionReglaFalsa:
    """Crea una fila de estancamiento con accion sin_cambio y el intervalo conservado."""
    inferior, superior, valor_inferior, valor_superior = extremos
    aproximacion, valor_aproximacion = muestra
    return IteracionReglaFalsa(
        i=indice,
        extremo_izquierdo=inferior,
        extremo_derecho=superior,
        valor_izquierdo=valor_inferior,
        valor_derecho=valor_superior,
        aproximacion=aproximacion,
        valor_aproximacion=valor_aproximacion,
        residuo=abs(valor_aproximacion),
        ancho=ancho_intervalo(inferior, superior),
        peso_secante=0.0,
        error_relativo_porcentual=None,
        signo_producto=signo_producto(valor_inferior, valor_aproximacion),
        accion="sin_cambio",
        intervalo_siguiente=intervalo,
        motivo_parada="estancamiento_numerico",
    )


def construir_resultado(
    entrada: EntradaReglaFalsa,
    motivo: str,
    iteraciones: Sequence[IteracionReglaFalsa],
) -> ResultadoReglaFalsa:
    """Devuelve un cierre coherente con la ultima fila."""
    estado, codigo, mensaje = _CIERRES[motivo]
    ultima = iteraciones[-1]
    return ResultadoReglaFalsa(
        entrada=entrada,
        estado=estado,
        mensaje=mensaje,
        codigo_diagnostico=codigo,
        motivo_parada=motivo,
        aproximacion=ultima.aproximacion,
        residuo=ultima.residuo,
        intervalo_final=ultima.intervalo_siguiente,
        iteraciones=tuple(iteraciones),
        iteraciones_totales=len(iteraciones),
        advertencias=entrada.advertencias,
    )


def construir_error(
    error: ValueError,
    iteraciones: Sequence[IteracionReglaFalsa] = (),
    codigo: str = "EXPRESION_INVALIDA",
    motivo: str = "expresion_invalida",
) -> ResultadoReglaFalsa:
    """Conserva la traza valida y clasifica el error sin publicar aproximaciones."""
    if isinstance(error, ErrorNoFinito):
        codigo = "EVALUACION_NO_FINITA"
        motivo = "evaluacion_invalida"
    elif isinstance(error, ErrorDominio):
        codigo = "DOMINIO_INVALIDO"
        motivo = "evaluacion_invalida"

    return ResultadoReglaFalsa(
        entrada=None,
        estado="ERROR",
        mensaje=str(error),
        codigo_diagnostico=getattr(error, "codigo", codigo),
        motivo_parada=motivo,
        aproximacion=None,
        residuo=None,
        intervalo_final=None,
        iteraciones=tuple(iteraciones),
        iteraciones_totales=len(iteraciones),
    )
