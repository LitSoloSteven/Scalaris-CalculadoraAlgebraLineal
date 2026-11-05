"""Diagnósticos del motor y contexto de evaluaciones sin valores no representables."""
from collections.abc import Callable, Sequence
from dataclasses import replace

from .contrato_biseccion import (
    CONTINUIDAD_CONDICIONAL, ContextoFallo, DiagnosticoBiseccion, EntradaBiseccion,
    EvaluacionExtremo, IteracionBiseccion, ResultadoBiseccion,
)
from .discontinuidades import calificar_discontinuidad
from .dominio_intervalo import comprobar_dominio_intervalo
from .evaluador_funcion import evaluar
from .traza_biseccion import construir_error
from .sugerencias_dominio import sugerir_acciones


def completar_diagnostico(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> ResultadoBiseccion:
    """Completa la evidencia de la traza y añade normalización y continuidad condicionada."""
    resultado = calificar_discontinuidad(resultado)
    diagnostico = resultado.diagnostico or {
        "codigo": resultado.codigo_diagnostico, "origen": "cierre", "mensaje": resultado.mensaje}
    advertencias = tuple(dict.fromkeys(entrada.advertencias + resultado.advertencias))
    return replace(resultado, diagnostico=diagnostico, advertencias=advertencias,
                   metricas={"continuidad": CONTINUIDAD_CONDICIONAL, **resultado.metricas},
                   sugerencias=sugerir_acciones(entrada, resultado), unidad_angular=entrada.unidad_angular)


def error_contextual(error: ValueError, contexto: ContextoFallo,
                     iteraciones: Sequence[IteracionBiseccion] = ()) -> ResultadoBiseccion:
    """Clasifica un fallo y conserva contexto y filas previas sin atribuirle una raíz."""
    resultado = construir_error(error, iteraciones)
    diagnostico = DiagnosticoBiseccion(codigo=resultado.codigo_diagnostico,
                                       origen=contexto["etapa"], mensaje=resultado.mensaje)
    return replace(resultado, diagnostico=diagnostico, contexto_fallo=contexto,
                   intervalo_final=contexto.get("intervalo_valido"))


def evaluar_extremos(funcion: Callable[[float], float], intervalo: tuple[float, float]) -> tuple[EvaluacionExtremo, ...]:
    """Intenta ambos extremos independientemente y devuelve sus valores o códigos de fallo."""
    return tuple(_evaluar_extremo(funcion, abscisa) for abscisa in intervalo)


def error_extremos(evaluaciones: tuple[EvaluacionExtremo, ...]) -> ResultadoBiseccion | None:
    """Devuelve el primer fallo con ambos diagnósticos; un extremo cero no oculta al inválido."""
    fallos = [evaluacion for evaluacion in evaluaciones if evaluacion["codigo"]]
    if not fallos:
        return None
    primero = fallos[0]
    return ResultadoBiseccion(
        estado="ERROR", mensaje=primero["mensaje"], codigo_diagnostico=primero["codigo"],
        motivo_parada="evaluacion_invalida", metricas={"iteraciones_totales": 0},
        diagnostico={"codigo": primero["codigo"], "origen": "extremos", "mensaje": primero["mensaje"]},
        contexto_fallo={"etapa": "extremos", "x_fallo": primero["abscisa"],
                        "intervalo_valido": None, "extremos": evaluaciones},
    )


def diagnostico_interior(expresion: str, intervalo: tuple[float, float], *, unidad_angular: str = "radianes") -> DiagnosticoBiseccion | None:
    """Consulta restricciones estructurales; no afirma haber evaluado su ubicación."""
    try:
        comprobar_dominio_intervalo(expresion, intervalo, unidad_angular=unidad_angular)
    except ValueError as error:
        resultado = construir_error(error)
        return {"codigo": resultado.codigo_diagnostico, "origen": "estructura", "mensaje": resultado.mensaje}
    return None


def _evaluar_extremo(funcion: Callable[[float], float], abscisa: float) -> EvaluacionExtremo:
    try:
        return {"abscisa": abscisa, "valor": evaluar(funcion, abscisa), "codigo": "", "mensaje": ""}
    except ValueError as error:
        resultado = construir_error(error)
        return {"abscisa": abscisa, "valor": None, "codigo": resultado.codigo_diagnostico, "mensaje": resultado.mensaje}
