"""Motor de bisección con control de dominio, resolución y traza numérica."""
from collections.abc import Callable
from dataclasses import asdict, replace

from .aritmetica_biseccion import punto_medio
from .contrato_biseccion import EntradaBiseccion, IteracionBiseccion, ResultadoBiseccion, validar_entrada
from .decision_biseccion import signo_producto
from .diagnostico_biseccion import IntervaloPreparado, completar_diagnostico, error_contextual, preparar_intervalo
from .evaluador_funcion import compilar, evaluar
from .gramatica_funcion import analizar_expresion
from .parada_biseccion import completar_criterio, motivo_criterio
from .traza_biseccion import construir_error, construir_resultado, crear_iteracion, registrar_accion
from .unidades_angulares import opciones_unidad


def biseccion(entrada: EntradaBiseccion, *, cero_preferido: float | None = None) -> ResultadoBiseccion:
    """Resuelve la entrada y prioriza el cero elegido si ambos extremos evalúan a cero."""
    try:
        if not isinstance(entrada, EntradaBiseccion):
            raise ValueError("La entrada debe cumplir el contrato de bisección.")
        entrada = validar_entrada(asdict(entrada))
    except ValueError as error:
        return construir_error(error, codigo="ENTRADA_INVALIDA")
    try:
        funcion = compilar(entrada.expresion, **opciones_unidad(entrada.unidad_angular))
        arbol = analizar_expresion(entrada.expresion)
    except ValueError as error:
        fallo = error_contextual(error, {"etapa": "sintaxis", "x_fallo": None, "intervalo_valido": None})
        return completar_diagnostico(entrada, completar_criterio(entrada, fallo))
    return resolver_intervalo_preparado(entrada, funcion, preparar_intervalo(entrada, funcion, arbol), cero_preferido)


def resolver_intervalo_preparado(entrada: EntradaBiseccion, funcion: Callable[[float], float],
                                 preparado: IntervaloPreparado, cero_preferido: float | None) -> ResultadoBiseccion:
    """Resuelve usando las evaluaciones iniciales obtenidas por la operación del servidor."""
    resultado = preparado.fallo or _resolver_intervalo(entrada, funcion, preparado, cero_preferido)
    resultado = replace(resultado, informe_continuidad=preparado.informe)
    return completar_diagnostico(entrada, completar_criterio(entrada, resultado))


def _resolver_intervalo(entrada: EntradaBiseccion, funcion: Callable[[float], float],
                        preparado: IntervaloPreparado, cero_preferido: float | None) -> ResultadoBiseccion:
    intervalo = preparado.intervalo
    extremos = (*intervalo, *(evaluacion["valor"] for evaluacion in preparado.evaluaciones))
    diagnostico = preparado.restriccion
    inicial = _validar_extremos(entrada, extremos, cero_preferido)
    if diagnostico and preparado.admite_cero and inicial is not None:
        return replace(inicial, diagnostico=diagnostico,
                       advertencias=("Continuidad no certificada: " + diagnostico["mensaje"],))
    if diagnostico is not None:
        return ResultadoBiseccion(
            estado="ERROR", mensaje=diagnostico["mensaje"], codigo_diagnostico=diagnostico["codigo"],
            motivo_parada="evaluacion_invalida", intervalo_final=intervalo, diagnostico=diagnostico,
            metricas={"iteraciones_totales": 0},
            contexto_fallo={"etapa": "estructura", "x_fallo": None, "intervalo_valido": intervalo})
    return inicial if inicial is not None else _iterar(entrada, funcion, extremos)


def _validar_extremos(entrada: EntradaBiseccion, extremos: tuple,
                      cero_preferido: float | None) -> ResultadoBiseccion | None:
    inferior, superior, valor_inferior, valor_superior = extremos
    if valor_inferior == 0 or valor_superior == 0:
        preferir_superior = valor_superior == 0 and cero_preferido == superior
        raiz = superior if preferir_superior or valor_inferior != 0 else inferior
        return construir_resultado(entrada, (inferior, superior), (), "raiz_exacta", (raiz, 0))
    if signo_producto(valor_inferior, valor_superior) == 1:
        return ResultadoBiseccion(
            estado="SIN_CAMBIO_DE_SIGNO", mensaje="Los valores f(a) y f(b) tienen el mismo signo. Elige otro intervalo.",
            error_absoluto=entrada.error_absoluto, codigo_diagnostico="SIN_CAMBIO_DE_SIGNO")
    return None


def _iterar(entrada: EntradaBiseccion, funcion: Callable[[float], float], extremos: tuple) -> ResultadoBiseccion:
    iteraciones = []
    previo = None
    contexto = {"etapa": "capacidad", "x_fallo": None, "intervalo_valido": extremos[:2]}
    try:
        for indice in range(1, entrada.limite_iteraciones + 1):
            inferior, superior = extremos[:2]
            contexto.update(etapa="capacidad", x_fallo=None, intervalo_valido=extremos[:2])
            abscisa = punto_medio(inferior, superior)
            contexto.update(etapa="iteracion", x_fallo=abscisa)
            valor = _evaluar_medio(funcion, abscisa, extremos)
            contexto.update(etapa="capacidad", x_fallo=None)
            fila = crear_iteracion(indice, extremos, (abscisa, valor), previo)
            motivo = _motivo_parada(entrada, fila)
            fila = registrar_accion(fila, motivo)
            iteraciones.append(fila)
            if motivo:
                break
            extremos = _actualizar_intervalo(fila)
            previo = abscisa
        return construir_resultado(entrada, (inferior, superior), iteraciones, motivo, (abscisa, valor))
    except ValueError as error:
        return error_contextual(error, contexto, iteraciones)


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


def _actualizar_intervalo(fila: IteracionBiseccion) -> tuple[float, float, float, float]:
    if fila.accion == "reemplazar_b":
        return fila.extremo_izquierdo, fila.c, fila.f_a, fila.f_c
    return fila.c, fila.extremo_derecho, fila.f_c, fila.f_b
