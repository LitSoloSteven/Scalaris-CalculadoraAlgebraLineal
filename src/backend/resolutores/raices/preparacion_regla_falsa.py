"""Preparacion del intervalo y diagnostico previo del motor de regla falsa."""
import ast
from collections.abc import Callable
from dataclasses import dataclass

from .cobertura_continuidad import cubre_intervalo_cerrado
from .contrato_biseccion import EvaluacionExtremo
from .contrato_continuidad import InformeContinuidad
from .contrato_regla_falsa import (
    DiagnosticoReglaFalsa,
    EntradaReglaFalsa,
    IteracionReglaFalsa,
    ResultadoReglaFalsa,
)
from .diagnostico_biseccion import error_extremos, evaluar_extremos
from .dominio_intervalo import comprobar_dominio_arbol
from .evaluador_funcion import compilar
from .gramatica_funcion import analizar_expresion
from .informe_continuidad import crear_informe, observacion
from .traza_regla_falsa import construir_error
from .unidades_angulares import opciones_unidad
from .validacion_regla_falsa import validar_entrada_regla_falsa


@dataclass(frozen=True)
class IntervaloReglaFalsaPreparado:
    """Evaluaciones iniciales y diagnostico reutilizables por el motor de regla falsa."""

    entrada: EntradaReglaFalsa
    funcion: Callable[[float], float]
    arbol: ast.Expression
    intervalo: tuple[float, float]
    evaluaciones: tuple[EvaluacionExtremo, ...]
    fallo: ResultadoReglaFalsa | None
    restriccion: DiagnosticoReglaFalsa | None
    admite_cero: bool
    informe: InformeContinuidad


def preparar_intervalo_regla_falsa(entrada: EntradaReglaFalsa) -> IntervaloReglaFalsaPreparado:
    """Compila una vez, evalua extremos y calcula continuidad; revalida la entrada."""
    if not isinstance(entrada, EntradaReglaFalsa):
        raise ValueError("La entrada debe cumplir el contrato de regla falsa.")
    canonica = validar_entrada_regla_falsa(_datos_entrada(entrada))
    try:
        funcion = compilar(canonica.expresion, **opciones_unidad(canonica.unidad_angular))
        arbol = analizar_expresion(canonica.expresion)
    except ValueError as error:
        fallo = _error_contextual_regla_falsa(
            error, {"etapa": "sintaxis", "x_fallo": None, "intervalo_valido": None}
        )
        return _preparado_error(canonica, fallo)
    return _construir_preparado(canonica, funcion, arbol)


def _construir_preparado(
    entrada: EntradaReglaFalsa, funcion: Callable[[float], float], arbol: ast.Expression
) -> IntervaloReglaFalsaPreparado:
    intervalo = (entrada.extremo_izquierdo, entrada.extremo_derecho)
    evaluaciones = evaluar_extremos(funcion, intervalo)
    fallo_extremos = error_extremos(evaluaciones)
    restriccion = None if fallo_extremos else _diagnosticar_arbol(arbol, intervalo, entrada.unidad_angular)
    admite_cero = fallo_extremos is None and any(
        evaluacion["valor"] == 0 for evaluacion in evaluaciones
    )
    if restriccion and admite_cero:
        admite_cero = not any(
            _diagnosticar_arbol(arbol, (extremo, extremo), entrada.unidad_angular) for extremo in intervalo
        )
    evidencia = _evidencia_inicial(arbol, intervalo, evaluaciones, fallo_extremos, restriccion)
    informe = crear_informe(intervalo, entrada.unidad_angular, evidencia, admite_cero)
    fallo = _error_extremos_regla_falsa(entrada, evaluaciones) if fallo_extremos else None
    return IntervaloReglaFalsaPreparado(
        entrada=entrada, funcion=funcion, arbol=arbol, intervalo=intervalo,
        evaluaciones=evaluaciones, fallo=fallo, restriccion=restriccion,
        admite_cero=admite_cero, informe=informe,
    )


def _datos_entrada(entrada: EntradaReglaFalsa) -> dict:
    return {
        "expresion": entrada.expresion,
        "extremo_izquierdo": entrada.extremo_izquierdo,
        "extremo_derecho": entrada.extremo_derecho,
        "tolerancia": entrada.tolerancia,
        "limite_iteraciones": entrada.limite_iteraciones,
        "intervalo_invertido": entrada.intervalo_invertido,
        "unidad_angular": entrada.unidad_angular,
    }


def _diagnosticar_arbol(
    arbol: ast.Expression, intervalo: tuple[float, float], unidad: str
) -> DiagnosticoReglaFalsa | None:
    try:
        comprobar_dominio_arbol(arbol, intervalo, unidad)
    except ValueError as error:
        base = construir_error(error, ())
        return {"codigo": base.codigo_diagnostico, "origen": "estructura", "mensaje": base.mensaje}
    return None


def _evidencia_inicial(
    arbol: ast.Expression,
    intervalo: tuple[float, float],
    evaluaciones: tuple[EvaluacionExtremo, ...],
    fallo_extremos,
    restriccion: DiagnosticoReglaFalsa | None,
):
    if fallo_extremos:
        fallos = tuple(
            observacion("FALLO_EXTREMO", evaluacion["codigo"], intervalo,
                        evaluacion["mensaje"], evaluacion["abscisa"])
            for evaluacion in evaluaciones if evaluacion["codigo"]
        )
        return fallos or (
            observacion("ANALISIS_INSUFICIENTE", fallo_extremos.codigo_diagnostico,
                        intervalo, fallo_extremos.mensaje),
        )
    if restriccion:
        return (
            observacion("RESTRICCION_ESTRUCTURAL", restriccion["codigo"],
                        intervalo, restriccion["mensaje"]),
        )
    if cubre_intervalo_cerrado(arbol):
        return (
            observacion("COBERTURA_ESTRUCTURAL", "CONTINUIDAD_ESTRUCTURAL_CONFIRMADA",
                        intervalo, "Las operaciones polinomicas cubren ambos extremos y el interior."),
        )
    return (
        observacion("ANALISIS_INSUFICIENTE", "COBERTURA_INSUFICIENTE",
                    intervalo, "El analisis disponible no cubre todas las operaciones de la expresion."),
    )


def _preparado_error(
    entrada: EntradaReglaFalsa, fallo: ResultadoReglaFalsa
) -> IntervaloReglaFalsaPreparado:
    intervalo = (entrada.extremo_izquierdo, entrada.extremo_derecho)
    evidencia = (
        observacion("ANALISIS_INSUFICIENTE", fallo.codigo_diagnostico,
                    intervalo, fallo.mensaje),
    )
    informe = crear_informe(intervalo, entrada.unidad_angular, evidencia, False)
    return IntervaloReglaFalsaPreparado(
        entrada=entrada, funcion=_funcion_nula, arbol=ast.parse("0", mode="eval"),
        intervalo=intervalo, evaluaciones=(), fallo=fallo, restriccion=None,
        admite_cero=False, informe=informe,
    )


def _funcion_nula(_valor: float) -> float:
    """Sustituye a la funcion real cuando la captura no es compilable; el motor no debe usarla."""
    return 0.0


def _error_extremos_regla_falsa(
    entrada: EntradaReglaFalsa, evaluaciones: tuple[EvaluacionExtremo, ...]
) -> ResultadoReglaFalsa | None:
    fallos = [evaluacion for evaluacion in evaluaciones if evaluacion["codigo"]]
    if not fallos:
        return None
    primero = fallos[0]
    return ResultadoReglaFalsa(
        entrada=entrada,
        estado="ERROR",
        mensaje=primero["mensaje"],
        codigo_diagnostico=primero["codigo"],
        motivo_parada="evaluacion_invalida",
        aproximacion=None,
        residuo=None,
        intervalo_final=None,
        iteraciones=(),
        iteraciones_totales=0,
        advertencias=entrada.advertencias,
        contexto_fallo={"etapa": "extremos", "x_fallo": primero["abscisa"],
                        "intervalo_valido": None, "extremos": evaluaciones},
    )


def _error_contextual_regla_falsa(
    error: ValueError, contexto: dict,
    iteraciones: tuple[IteracionReglaFalsa, ...] = (),
) -> ResultadoReglaFalsa:
    base = construir_error(error, iteraciones)
    return ResultadoReglaFalsa(
        entrada=None,
        estado=base.estado,
        mensaje=base.mensaje,
        codigo_diagnostico=base.codigo_diagnostico,
        motivo_parada=base.motivo_parada,
        aproximacion=None,
        residuo=None,
        intervalo_final=contexto.get("intervalo_valido"),
        iteraciones=iteraciones,
        iteraciones_totales=len(iteraciones),
        contexto_fallo=contexto,
    )