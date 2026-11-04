"""Motor de bisección con control de dominio, resolución y traza numérica."""
import math
from collections.abc import Callable
from dataclasses import asdict, replace

from .aritmetica_biseccion import cota_intervalo, punto_medio
from .contrato_biseccion import EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion, validar_entrada
from .diagnostico_biseccion import diagnostico_interior, error_contextual, error_extremos, evaluar_extremos
from .evaluador_funcion import compilar, evaluar
from .parada_biseccion import completar_criterio, motivo_criterio
from .traza_biseccion import construir_error, construir_resultado, crear_iteracion


def biseccion(entrada: EntradaBiseccion) -> ResultadoBiseccion:
    """Resuelve una entrada validada y devuelve estado, diagnóstico y traza sin lanzar errores numéricos."""
    try:
        if not isinstance(entrada, EntradaBiseccion):
            raise ValueError("La entrada debe cumplir el contrato de bisección.")
        entrada = validar_entrada(asdict(entrada))
    except ValueError as error:
        return construir_error(error, codigo="ENTRADA_INVALIDA")
    return completar_criterio(entrada, _resolver_entrada(entrada))


def _resolver_entrada(entrada: EntradaBiseccion) -> ResultadoBiseccion:
    try:
        funcion = compilar(entrada.expresion)
    except ValueError as error:
        return error_contextual(error, {"etapa": "sintaxis", "x_fallo": None, "intervalo_valido": None})
    intervalo = entrada.extremo_izquierdo, entrada.extremo_derecho
    evaluaciones = evaluar_extremos(funcion, intervalo)
    fallo = error_extremos(evaluaciones)
    if fallo is not None:
        return fallo
    try:
        cota_intervalo(*intervalo)
    except ValueError as error:
        return error_contextual(error, {"etapa": "capacidad", "x_fallo": None,
                                        "intervalo_valido": None, "extremos": evaluaciones})
    extremos = (*intervalo, *(evaluacion["valor"] for evaluacion in evaluaciones))
    return _resolver_intervalo(entrada, funcion, extremos)


def _resolver_intervalo(entrada: EntradaBiseccion, funcion: Callable[[float], float], extremos: tuple) -> ResultadoBiseccion:
    intervalo = extremos[:2]
    diagnostico = diagnostico_interior(entrada.expresion, intervalo)
    inicial = _validar_extremos(entrada, extremos)
    if inicial is not None and inicial.motivo_parada == "raiz_exacta":
        if diagnostico is not None:
            return replace(inicial, diagnostico=diagnostico,
                           advertencias=("Continuidad no certificada: " + diagnostico["mensaje"],))
        return inicial
    if diagnostico is not None:
        return ResultadoBiseccion(
            estado="ERROR", mensaje=diagnostico["mensaje"], codigo_diagnostico=diagnostico["codigo"],
            motivo_parada="evaluacion_invalida", intervalo_final=intervalo, diagnostico=diagnostico,
            metricas={"iteraciones_totales": 0},
            contexto_fallo={"etapa": "estructura", "x_fallo": None, "intervalo_valido": intervalo})
    return inicial if inicial is not None else _iterar(entrada, funcion, extremos)


def _validar_extremos(entrada: EntradaBiseccion, extremos: tuple) -> ResultadoBiseccion | None:
    inferior, superior, valor_inferior, valor_superior = extremos
    if valor_inferior == 0 or valor_superior == 0:
        raiz = inferior if valor_inferior == 0 else superior
        return construir_resultado(entrada, (inferior, superior), (), "raiz_exacta", (raiz, 0))
    if math.copysign(1, valor_inferior) == math.copysign(1, valor_superior):
        return ResultadoBiseccion(
            estado="SIN_CAMBIO_DE_SIGNO", mensaje="Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
            error_absoluto=entrada.error_absoluto, codigo_diagnostico="SIN_CAMBIO_DE_SIGNO")
    return None


def _iterar(entrada: EntradaBiseccion, funcion: Callable[[float], float], extremos: tuple) -> ResultadoBiseccion:
    iteraciones = []
    previo = None
    abscisa = None
    try:
        for indice in range(1, entrada.limite_iteraciones + 1):
            inferior, superior, valor_inferior, valor_superior = extremos
            abscisa = punto_medio(inferior, superior)
            valor = _evaluar_medio(funcion, abscisa, extremos)
            fila = crear_iteracion(indice, extremos, (abscisa, valor), previo)
            iteraciones.append(fila)
            motivo = _motivo_parada(entrada, fila)
            if motivo:
                break
            extremos = _actualizar_intervalo(extremos, (abscisa, valor))
            previo = abscisa
        return construir_resultado(entrada, (inferior, superior), iteraciones, motivo, (abscisa, valor))
    except ValueError as error:
        return error_contextual(error, {"etapa": "iteracion", "x_fallo": abscisa,
                                        "intervalo_valido": extremos[:2]}, iteraciones)


def _evaluar_medio(funcion: Callable[[float], float], abscisa: float, extremos: tuple) -> float:
    inferior, superior, valor_inferior, valor_superior = extremos
    if abscisa == inferior:
        return valor_inferior
    if abscisa == superior:
        return valor_superior
    return evaluar(funcion, abscisa)


def _motivo_parada(entrada: EntradaBiseccion, fila: IteracionBiseccion) -> str:
    if fila.f_c == 0:
        return "raiz_exacta"
    if fila.c in (fila.extremo_izquierdo, fila.extremo_derecho):
        return "estancamiento"
    motivo = motivo_criterio(entrada.criterio_activo, fila)
    if motivo:
        return motivo
    return "limite_iteraciones" if fila.i == entrada.limite_iteraciones else ""


def _actualizar_intervalo(extremos: tuple, medio: tuple[float, float]) -> tuple:
    inferior, superior, valor_inferior, valor_superior = extremos
    abscisa, valor = medio
    if math.copysign(1, valor_inferior) != math.copysign(1, valor):
        return inferior, abscisa, valor_inferior, valor
    return abscisa, superior, valor, valor_superior
