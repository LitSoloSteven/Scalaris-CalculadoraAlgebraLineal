"""Motor iterativo de la secante con evaluación segura y paradas controladas."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace

from ..evaluador_funcion import compilar
from .aritmetica_abierta import (
    advertencias_por_cambio,
    criterio_parada,
    denominador_utilizable,
    error_relativo_porcentual,
    evaluar_con_guarda,
    paso_representable,
)
from .contrato_abiertos import (
    EntradaMetodoAbierto,
    IteracionMetodoAbierto,
    ResultadoMetodoAbierto,
    resultado_convergencia,
    resultado_error,
    resultado_evaluacion,
    resultado_fallo,
    resultado_inicial,
    resultado_limite,
)
from .validacion_abiertos import preparar_entrada_abierta

Funcion = Callable[[float], float]
PuntosSecante = tuple[float, float, float, float]


@dataclass(frozen=True)
class _PasoSecante:
    x_siguiente: float
    f_siguiente: float
    error: float
    error_relativo: float | None


def secante(entrada: EntradaMetodoAbierto | Mapping[str, object]) -> ResultadoMetodoAbierto:
    """Ejecuta la secante con una captura o entrada tipada.

    Args:
        entrada: Datos del método, incluidos expresión, dos puntos iniciales y límites.

    Returns:
        Resultado con estado, diagnóstico y traza; una entrada inválida produce ERROR.
    """
    try:
        tipada = preparar_entrada_abierta(entrada, "secante")
    except ValueError as error:
        return resultado_error("secante", "ENTRADA_INVALIDA", str(error))
    try:
        funcion = compilar(tipada.expresion)
    except ValueError as error:
        return resultado_error("secante", "ENTRADA_INVALIDA", str(error), entrada=tipada)
    return _iterar_secante(tipada, funcion)


def _iterar_secante(entrada: EntradaMetodoAbierto, funcion: Funcion) -> ResultadoMetodoAbierto:
    puntos = _evaluar_puntos(entrada, funcion)
    if isinstance(puntos, ResultadoMetodoAbierto):
        return puntos
    x0, f0, x1, f1 = puntos
    if abs(f0) < entrada.tolerancia:
        return resultado_inicial("secante", entrada, x0, f0)
    if abs(f1) < entrada.tolerancia:
        return resultado_inicial("secante", entrada, x1, f1)
    iteraciones: list[IteracionMetodoAbierto] = []
    for i in range(1, entrada.limite_iteraciones + 1):
        paso = _paso_secante(entrada, funcion, puntos)
        if isinstance(paso, ResultadoMetodoAbierto):
            return replace(paso, iteraciones=tuple(iteraciones), iteraciones_totales=len(iteraciones))
        criterio = criterio_parada(paso.f_siguiente, paso.error, entrada.tolerancia)
        iteraciones.append(_fila_secante(puntos, paso, i, criterio))
        if criterio:
            return _exito_secante(entrada, iteraciones, paso, criterio)
        x0, f0, x1, f1 = x1, f1, paso.x_siguiente, paso.f_siguiente
        puntos = (x0, f0, x1, f1)
    return resultado_limite("secante", entrada, tuple(iteraciones), raiz=x1, residuo=abs(f1))


def _evaluar_puntos(
    entrada: EntradaMetodoAbierto, funcion: Funcion
) -> PuntosSecante | ResultadoMetodoAbierto:
    """Evalúa los dos puntos iniciales o devuelve el error de evaluación."""
    f0, detalle = evaluar_con_guarda(funcion, entrada.x0)
    if detalle is not None:
        return resultado_evaluacion("secante", entrada.x0, detalle, entrada=entrada)
    f1, detalle = evaluar_con_guarda(funcion, entrada.x1)
    if detalle is not None:
        return resultado_evaluacion("secante", entrada.x1, detalle, entrada=entrada)
    return entrada.x0, f0, entrada.x1, f1


def _paso_secante(
    entrada: EntradaMetodoAbierto, funcion: Funcion, puntos: PuntosSecante
) -> _PasoSecante | ResultadoMetodoAbierto:
    """Calcula una iteración completa o devuelve el fallo que la impide."""
    x0, f0, x1, f1 = puntos
    if not denominador_utilizable(f1, f0):
        return resultado_fallo(
            "secante",
            "DENOMINADOR_NULO",
            "DENOMINADOR_NULO",
            "El denominador de la secante es nulo o demasiado pequeño.",
            entrada=entrada,
            contexto_fallo={
                "x0": x0,
                "x1": x1,
                "f0": f0,
                "f1": f1,
                "denominador": f1 - f0,
            },
        )
    denominador = f1 - f0
    x_siguiente = x1 - f1 * (x1 - x0) / denominador
    if not paso_representable(x_siguiente):
        return resultado_fallo(
            "secante",
            "DIVERGENCIA",
            "DIVERGENCIA",
            f"La iteración produjo una aproximación no representable en x = {x_siguiente!r}.",
            entrada=entrada,
            contexto_fallo={"x0": x0, "x1": x1, "x_siguiente": repr(x_siguiente)},
        )
    f_siguiente, detalle = evaluar_con_guarda(funcion, x_siguiente)
    if detalle is not None:
        return resultado_evaluacion("secante", x_siguiente, detalle, entrada=entrada)
    return _PasoSecante(
        x_siguiente=x_siguiente,
        f_siguiente=f_siguiente,
        error=abs(x_siguiente - x1),
        error_relativo=error_relativo_porcentual(x_siguiente, x1),
    )


def _fila_secante(
    puntos: PuntosSecante,
    paso: _PasoSecante,
    i: int,
    criterio: str,
) -> IteracionMetodoAbierto:
    x0, f0, x1, f1 = puntos
    return IteracionMetodoAbierto(
        i=i,
        x_anterior=x0,
        f_x_anterior=f0,
        x_n=x1,
        f_x_n=f1,
        derivada=None,
        x_siguiente=paso.x_siguiente,
        f_x_siguiente=paso.f_siguiente,
        residuo=abs(paso.f_siguiente),
        error_absoluto=paso.error,
        error_relativo_porcentual=paso.error_relativo,
        criterio=criterio,
    )


def _exito_secante(
    entrada: EntradaMetodoAbierto,
    iteraciones: list[IteracionMetodoAbierto],
    paso: _PasoSecante,
    criterio: str,
) -> ResultadoMetodoAbierto:
    advertencias = advertencias_por_cambio(paso.f_siguiente, entrada.tolerancia, criterio)
    return resultado_convergencia(
        "secante",
        entrada,
        tuple(iteraciones),
        criterio,
        raiz=paso.x_siguiente,
        residuo=abs(paso.f_siguiente),
        advertencias=advertencias,
    )
