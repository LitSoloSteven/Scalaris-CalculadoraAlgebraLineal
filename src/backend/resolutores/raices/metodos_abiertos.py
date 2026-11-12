"""Métodos abiertos mínimos: Newton-Raphson y secante."""
from dataclasses import dataclass
import math

from .evaluador_funcion import compilar, evaluar
from .unidades_angulares import opciones_unidad


@dataclass(frozen=True)
class IteracionAbierta:
    i: int
    x: float
    fx: float
    error: float | None
    derivada: float | None = None  # Guarda f'(x) en Newton o la pendiente en Secante


@dataclass(frozen=True)
class ResultadoAbierto:
    estado: str
    metodo: str
    mensaje: str
    raiz: float | None
    iteraciones: tuple[IteracionAbierta, ...]
    motivo: str = ""


def _error(mensaje: str, metodo: str, filas=()) -> ResultadoAbierto:
    return ResultadoAbierto("ERROR", metodo, mensaje, None, tuple(filas), "error")


def _funcion(expresion: str, unidad_angular: str):
    return compilar(expresion, **opciones_unidad(unidad_angular))


def newton_raphson(
    expresion: str,
    x0: float,
    *,
    tolerancia: float = 1e-6,
    limite_iteraciones: int = 100,
    unidad_angular: str = "radianes",
) -> ResultadoAbierto:
    """Newton-Raphson con derivada numérica central."""
    metodo = "newton"
    try:
        f = _funcion(expresion, unidad_angular)
    except ValueError as error:
        return _error(str(error), metodo)

    x = float(x0)
    filas: list[IteracionAbierta] = []

    for i in range(1, limite_iteraciones + 1):
        try:
            fx = evaluar(f, x)
            h = max(1e-7, abs(x) * 1e-7)
            derivada = (evaluar(f, x + h) - evaluar(f, x - h)) / (2 * h)
        except ValueError as error:
            return _error(str(error), metodo, filas)

        if abs(fx) < tolerancia:
            filas.append(IteracionAbierta(i, x, fx, None, derivada))
            return ResultadoAbierto(
                "EXITO", metodo, "Residuo menor que la tolerancia.", x, tuple(filas), "residuo"
            )

        if not math.isfinite(derivada) or abs(derivada) < 1e-15:
            return _error("La derivada numérica es cero o no finita.", metodo, filas)

        nuevo = x - fx / derivada
        if not math.isfinite(nuevo):
            return _error("Newton produjo un valor no finito.", metodo, filas)

        error = abs(nuevo - x)
        filas.append(IteracionAbierta(i, x, fx, error, derivada))

        if error < tolerancia:
            return ResultadoAbierto(
                "EXITO", metodo, "Cambio menor que la tolerancia.", nuevo, tuple(filas), "cambio"
            )

        x = nuevo

    return ResultadoAbierto(
        "LIMITE_ITERACIONES", metodo, "Se alcanzó el límite de iteraciones.", x, tuple(filas), "limite"
    )


def secante(
    expresion: str,
    x0: float,
    x1: float,
    *,
    tolerancia: float = 1e-6,
    limite_iteraciones: int = 100,
    unidad_angular: str = "radianes",
) -> ResultadoAbierto:
    """Secante clásica con dos puntos iniciales."""
    metodo = "secante"
    if x0 == x1:
        return _error("Los dos puntos iniciales deben ser distintos.", metodo)

    try:
        f = _funcion(expresion, unidad_angular)
        f_previo = evaluar(f, x0)
        f_actual = evaluar(f, x1)
    except ValueError as error:
        return _error(str(error), metodo)

    anterior, actual = float(x0), float(x1)
    filas: list[IteracionAbierta] = []

    for i in range(1, limite_iteraciones + 1):
        denominador = f_actual - f_previo
        if abs(denominador) < 1e-15:
            return _error("La secante tiene denominador cero.", metodo, filas)

        # La pendiente de la recta secante
        pendiente = denominador / (actual - anterior)
        nuevo = actual - f_actual / pendiente
        
        if not math.isfinite(nuevo):
            return _error("La secante produjo un valor no finito.", metodo, filas)

        try:
            f_nuevo = evaluar(f, nuevo)
        except ValueError as error:
            return _error(str(error), metodo, filas)

        error = abs(nuevo - actual)
        filas.append(IteracionAbierta(i, actual, f_actual, error, pendiente))

        if abs(f_nuevo) < tolerancia:
            return ResultadoAbierto(
                "EXITO", metodo, "Residuo menor que la tolerancia.", nuevo, tuple(filas), "residuo"
            )
        if error < tolerancia:
            return ResultadoAbierto(
                "EXITO", metodo, "Cambio menor que la tolerancia.", nuevo, tuple(filas), "cambio"
            )

        anterior, actual = actual, nuevo
        f_previo, f_actual = f_actual, f_nuevo

    return ResultadoAbierto(
        "LIMITE_ITERACIONES", metodo, "Se alcanzó el límite de iteraciones.", actual, tuple(filas), "limite"
    )