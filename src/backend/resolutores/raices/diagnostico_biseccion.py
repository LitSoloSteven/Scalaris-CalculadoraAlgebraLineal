"""Diagnósticos del motor y contexto de evaluaciones sin valores no representables."""
import ast
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from .aritmetica_biseccion import cota_intervalo
from .cobertura_continuidad import cubre_intervalo_cerrado
from .contrato_biseccion import (
    CONTINUIDAD_CONDICIONAL, ContextoFallo, DiagnosticoBiseccion, EntradaBiseccion,
    EvaluacionExtremo, IteracionBiseccion, ResultadoBiseccion, validar_entrada,
)
from .contrato_continuidad import InformeContinuidad
from .discontinuidades import calificar_discontinuidad
from .dominio_intervalo import comprobar_dominio_arbol
from .evaluador_funcion import compilar, evaluar
from .gramatica_funcion import analizar_expresion
from .informe_continuidad import crear_informe, incorporar_traza, observacion
from .traza_biseccion import construir_error
from .sugerencias_dominio import sugerir_acciones
from .unidades_angulares import opciones_unidad


@dataclass(frozen=True)
class IntervaloPreparado:
    """Evaluaciones iniciales y diagnóstico reutilizables dentro de una sola operación."""

    intervalo: tuple[float, float]
    evaluaciones: tuple[EvaluacionExtremo, ...]
    fallo: ResultadoBiseccion | None
    restriccion: DiagnosticoBiseccion | None
    admite_cero: bool
    informe: InformeContinuidad


def analizar_continuidad_intervalo(expresion: str, intervalo: tuple[float, float], *,
                                   unidad_angular: str = "radianes",
                                   cero_preferido: float | None = None) -> InformeContinuidad:
    """Analiza el intervalo sin iterar; lanza ValueError para captura inválida."""
    if not isinstance(intervalo, tuple) or len(intervalo) != 2:
        raise ValueError("Introduce un intervalo de dos extremos.")
    entrada = validar_entrada(dict(expresion=expresion, extremo_izquierdo=intervalo[0],
                                   extremo_derecho=intervalo[1], decimales=0, unidad_angular=unidad_angular))
    if cero_preferido is not None and (type(cero_preferido) not in (int, float)
            or cero_preferido not in (entrada.extremo_izquierdo, entrada.extremo_derecho)):
        raise ValueError("El cero elegido debe ser un extremo del intervalo.")
    arbol = analizar_expresion(entrada.expresion)
    funcion = compilar(entrada.expresion, **opciones_unidad(entrada.unidad_angular))
    preparado = preparar_intervalo(entrada, funcion, arbol)
    return preparado.informe


def preparar_intervalo(entrada: EntradaBiseccion, funcion: Callable[[float], float],
                       arbol: ast.Expression) -> IntervaloPreparado:
    """Evalúa los extremos una vez y aplica el análisis del intervalo canónico."""
    intervalo = entrada.extremo_izquierdo, entrada.extremo_derecho
    unidad = entrada.unidad_angular
    evaluaciones = evaluar_extremos(funcion, intervalo)
    fallo = error_extremos(evaluaciones) or _error_cota(intervalo, evaluaciones)
    restriccion = None if fallo else _diagnosticar_arbol(arbol, intervalo, unidad)
    admite_cero = fallo is None and any(muestra["valor"] == 0 for muestra in evaluaciones)
    if restriccion and admite_cero:
        admite_cero = not any(_diagnosticar_arbol(arbol, (extremo, extremo), unidad) for extremo in intervalo)
    evidencia = _evidencia_inicial(arbol, intervalo, evaluaciones, fallo, restriccion)
    informe = crear_informe(intervalo, unidad, evidencia, admite_cero)
    return IntervaloPreparado(intervalo, evaluaciones, fallo, restriccion, admite_cero, informe)


def _error_cota(intervalo: tuple[float, float], evaluaciones: tuple[EvaluacionExtremo, ...]) -> ResultadoBiseccion | None:
    try:
        cota_intervalo(*intervalo)
    except ValueError as error:
        return error_contextual(error, {"etapa": "capacidad", "x_fallo": None,
                                        "intervalo_valido": None, "extremos": evaluaciones})
    return None


def _evidencia_inicial(arbol, intervalo, evaluaciones, fallo, restriccion):
    if fallo:
        fallos = tuple(observacion("FALLO_EXTREMO", muestra["codigo"], intervalo,
                                   muestra["mensaje"], muestra["abscisa"])
                       for muestra in evaluaciones if muestra["codigo"])
        return fallos or (observacion("ANALISIS_INSUFICIENTE", fallo.codigo_diagnostico, intervalo, fallo.mensaje),)
    if restriccion:
        return (observacion("RESTRICCION_ESTRUCTURAL", restriccion["codigo"], intervalo, restriccion["mensaje"]),)
    if cubre_intervalo_cerrado(arbol):
        return (observacion("COBERTURA_ESTRUCTURAL", "CONTINUIDAD_ESTRUCTURAL_CONFIRMADA", intervalo,
                            "Las operaciones polinómicas cubren ambos extremos y el interior."),)
    return (observacion("ANALISIS_INSUFICIENTE", "COBERTURA_INSUFICIENTE", intervalo,
                        "El análisis disponible no cubre todas las operaciones de la expresión."),)


def completar_diagnostico(entrada: EntradaBiseccion, resultado: ResultadoBiseccion) -> ResultadoBiseccion:
    """Completa la evidencia de la traza y añade normalización y continuidad condicionada."""
    resultado = calificar_discontinuidad(resultado)
    diagnostico = resultado.diagnostico or {
        "codigo": resultado.codigo_diagnostico, "origen": "cierre", "mensaje": resultado.mensaje}
    advertencias = tuple(dict.fromkeys(entrada.advertencias + resultado.advertencias))
    informe = resultado.informe_continuidad
    if informe is not None:
        informe = incorporar_traza(informe, resultado)
    return replace(resultado, diagnostico=diagnostico, advertencias=advertencias, informe_continuidad=informe,
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
        arbol = analizar_expresion(expresion)
        opciones_unidad(unidad_angular)
    except ValueError as error:
        return _diagnostico_estructural(error)
    return _diagnosticar_arbol(arbol, intervalo, unidad_angular)


def _diagnosticar_arbol(arbol: ast.Expression, intervalo: tuple[float, float], unidad: str) -> DiagnosticoBiseccion | None:
    try:
        comprobar_dominio_arbol(arbol, intervalo, unidad)
    except ValueError as error:
        return _diagnostico_estructural(error)
    return None


def _diagnostico_estructural(error: ValueError) -> DiagnosticoBiseccion:
    resultado = construir_error(error)
    return {"codigo": resultado.codigo_diagnostico, "origen": "estructura", "mensaje": resultado.mensaje}


def _evaluar_extremo(funcion: Callable[[float], float], abscisa: float) -> EvaluacionExtremo:
    try:
        return {"abscisa": abscisa, "valor": evaluar(funcion, abscisa), "codigo": "", "mensaje": ""}
    except ValueError as error:
        resultado = construir_error(error)
        return {"abscisa": abscisa, "valor": None, "codigo": resultado.codigo_diagnostico, "mensaje": resultado.mensaje}
