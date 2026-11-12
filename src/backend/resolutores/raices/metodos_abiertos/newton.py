"""Motor iterativo de Newton-Raphson con derivada simbólica y paradas controladas."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace

from ..evaluador_funcion import compilar
from .aritmetica_abierta import (
    advertencias_por_cambio,
    criterio_parada,
    derivada_utilizable,
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
from .derivada_simbolica import ErrorDerivadaDemasiadoGrande, derivar_expresion
from .validacion_abiertos import preparar_entrada_abierta

Funcion = Callable[[float], float]
FuncionesNewton = tuple[Funcion, Funcion, str]


@dataclass(frozen=True)
class _PasoNewton:
    x_siguiente: float
    f_siguiente: float
    derivada: float
    error: float
    error_relativo: float | None


def newton(entrada: EntradaMetodoAbierto | Mapping[str, object]) -> ResultadoMetodoAbierto:
    """Ejecuta Newton-Raphson con una captura o entrada tipada.

    Args:
        entrada: Datos del método, incluidos expresión, punto inicial y límites.

    Returns:
        Resultado con estado, diagnóstico y traza; una entrada inválida produce ERROR.
    """
    try:
        tipada = preparar_entrada_abierta(entrada, "newton")
    except ValueError as error:
        return resultado_error("newton", "ENTRADA_INVALIDA", str(error))
    try:
        funcion = compilar(tipada.expresion)
    except ValueError as error:
        return resultado_error("newton", "ENTRADA_INVALIDA", str(error), entrada=tipada)
    try:
        derivada_texto = derivar_expresion(tipada.expresion)
        funcion_derivada = compilar(derivada_texto)
    except ErrorDerivadaDemasiadoGrande as error:
        return resultado_error("newton", "DERIVADA_DEMASIADO_GRANDE", str(error), entrada=tipada)
    except ValueError as error:
        return resultado_error("newton", "DERIVADA_NO_DISPONIBLE", str(error), entrada=tipada)
    return _iterar_newton(tipada, (funcion, funcion_derivada, derivada_texto))


def _iterar_newton(entrada: EntradaMetodoAbierto, funciones: FuncionesNewton) -> ResultadoMetodoAbierto:
    funcion, funcion_derivada, derivada_texto = funciones
    actual = entrada.x0
    f_x, detalle = evaluar_con_guarda(funcion, actual)
    if detalle is not None:
        return resultado_evaluacion("newton", actual, detalle, entrada=entrada, derivada_expresion=derivada_texto)
    if abs(f_x) < entrada.tolerancia:
        return resultado_inicial("newton", entrada, actual, f_x, derivada_expresion=derivada_texto)
    iteraciones: list[IteracionMetodoAbierto] = []
    for i in range(1, entrada.limite_iteraciones + 1):
        paso = _paso_newton(entrada, funciones, actual, f_x)
        if isinstance(paso, ResultadoMetodoAbierto):
            return replace(paso, iteraciones=tuple(iteraciones), iteraciones_totales=len(iteraciones))
        criterio = criterio_parada(paso.f_siguiente, paso.error, entrada.tolerancia)
        iteraciones.append(_fila_newton(actual, f_x, paso, i, criterio))
        if criterio:
            return _exito_newton(entrada, iteraciones, paso, criterio, derivada_texto)
        actual, f_x = paso.x_siguiente, paso.f_siguiente
    return resultado_limite(
        "newton",
        entrada,
        tuple(iteraciones),
        raiz=actual,
        residuo=abs(f_x),
        derivada_expresion=derivada_texto,
    )


def _paso_newton(
    entrada: EntradaMetodoAbierto,
    funciones: FuncionesNewton,
    actual: float,
    f_x: float,
) -> _PasoNewton | ResultadoMetodoAbierto:
    funcion, funcion_derivada, derivada_texto = funciones
    derivada, detalle = evaluar_con_guarda(funcion_derivada, actual)
    if detalle is not None:
        return resultado_evaluacion("newton", actual, detalle, entrada=entrada, derivada_expresion=derivada_texto)
    if not derivada_utilizable(derivada, actual):
        return resultado_fallo(
            "newton",
            "DERIVADA_NULA",
            "DERIVADA_NULA",
            f"La derivada es nula o demasiado pequeña en x = {actual:g}.",
            entrada=entrada,
            derivada_expresion=derivada_texto,
            contexto_fallo={"x": actual, "f_x": f_x, "derivada": derivada},
        )
    x_siguiente = actual - f_x / derivada
    if not paso_representable(x_siguiente):
        return resultado_fallo(
            "newton",
            "DIVERGENCIA",
            "DIVERGENCIA",
            f"La iteración produjo una aproximación no representable en x = {x_siguiente!r}.",
            entrada=entrada,
            derivada_expresion=derivada_texto,
            contexto_fallo={
                "x": actual,
                "x_siguiente": repr(x_siguiente),
                "f_x": f_x,
                "derivada": derivada,
            },
        )
    f_siguiente, detalle = evaluar_con_guarda(funcion, x_siguiente)
    if detalle is not None:
        return resultado_evaluacion("newton", x_siguiente, detalle, entrada=entrada, derivada_expresion=derivada_texto)
    error = abs(x_siguiente - actual)
    return _PasoNewton(x_siguiente, f_siguiente, derivada, error, error_relativo_porcentual(x_siguiente, actual))


def _fila_newton(
    actual: float,
    f_x: float,
    paso: _PasoNewton,
    i: int,
    criterio: str,
) -> IteracionMetodoAbierto:
    return IteracionMetodoAbierto(
        i=i,
        x_anterior=None,
        f_x_anterior=None,
        x_n=actual,
        f_x_n=f_x,
        derivada=paso.derivada,
        x_siguiente=paso.x_siguiente,
        f_x_siguiente=paso.f_siguiente,
        residuo=abs(paso.f_siguiente),
        error_absoluto=paso.error,
        error_relativo_porcentual=paso.error_relativo,
        criterio=criterio,
    )


def _exito_newton(
    entrada: EntradaMetodoAbierto,
    iteraciones: list[IteracionMetodoAbierto],
    paso: _PasoNewton,
    criterio: str,
    derivada_texto: str,
) -> ResultadoMetodoAbierto:
    advertencias = advertencias_por_cambio(paso.f_siguiente, entrada.tolerancia, criterio)
    return resultado_convergencia(
        "newton",
        entrada,
        tuple(iteraciones),
        criterio,
        raiz=paso.x_siguiente,
        residuo=abs(paso.f_siguiente),
        derivada_expresion=derivada_texto,
        advertencias=advertencias,
    )
