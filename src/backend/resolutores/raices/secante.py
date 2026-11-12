"""Motor del método abierto de la secante para ecuaciones no lineales."""
from dataclasses import dataclass, field
import math
from typing import Literal

from .evaluador_funcion import compilar, evaluar
from .limites_raices import LIMITE_ITERACIONES_DEFECTO
from .unidades_angulares import validar_unidad_angular
from .validacion_raices import validar_expresion, validar_extremo, validar_limite_iteraciones


@dataclass(frozen=True, kw_only=True)
class EntradaSecante:
    """Datos iniciales y criterios de parada del método de la secante."""
    expresion: str
    x_anterior: float
    x_actual: float
    tolerancia: float = 1e-6
    limite_iteraciones: int = LIMITE_ITERACIONES_DEFECTO
    unidad_angular: Literal["radianes", "grados"] = "radianes"


@dataclass(frozen=True)
class IteracionSecante:
    """Valores calculados en una iteración, sin redondeo de presentación."""
    i: int
    x_anterior: float
    x_actual: float
    f_anterior: float
    f_actual: float
    x_siguiente: float
    f_siguiente: float
    error_absoluto: float
    error_relativo_porcentual: float | None


@dataclass(frozen=True)
class ResultadoSecante:
    """Resultado del cálculo y traza completa de las iteraciones válidas."""
    metodo: Literal["secante"] = field(default="secante", init=False)
    entrada: EntradaSecante | None = None
    estado: Literal["EXITO", "LIMITE_ITERACIONES", "ESTANCAMIENTO", "ERROR"] = "ERROR"
    mensaje: str = ""
    codigo_diagnostico: str = ""
    motivo_parada: str = ""
    aproximacion: float | None = None
    residuo: float | None = None
    iteraciones: tuple[IteracionSecante, ...] = ()
    iteraciones_totales: int = 0


def secante(entrada: EntradaSecante) -> ResultadoSecante:
    """Resuelve f(x)=0 mediante la secante; no exige intervalo ni cambio de signo."""
    try:
        entrada = _validar_entrada(entrada)
    except ValueError as error:
        return _error(None, error, "ENTRADA_INVALIDA", "entrada_invalida")

    try:
        funcion = compilar(entrada.expresion, unidad_angular=entrada.unidad_angular)
    except ValueError as error:
        return _error(entrada, error, "EXPRESION_INVALIDA", "expresion_invalida")

    x_anterior, x_actual = entrada.x_anterior, entrada.x_actual
    try:
        f_anterior = evaluar(funcion, x_anterior)
        f_actual = evaluar(funcion, x_actual)
    except ValueError as error:
        return _error(entrada, error, _codigo_evaluacion(error), "evaluacion_inicial")

    if f_anterior == 0:
        return _raiz_inicial(entrada, x_anterior)
    if f_actual == 0:
        return _raiz_inicial(entrada, x_actual)

    filas: list[IteracionSecante] = []
    for indice in range(1, entrada.limite_iteraciones + 1):
        denominador = f_actual - f_anterior
        if denominador == 0:
            return _error(
                entrada,
                ValueError("f(xₙ) y f(xₙ₋₁) son iguales; no se puede calcular la secante."),
                "DENOMINADOR_CERO",
                "denominador_cero",
                filas,
            )

        try:
            diferencia_x = x_actual - x_anterior
            siguiente = x_actual - (f_actual / denominador) * diferencia_x
            if not math.isfinite(siguiente):
                raise ValueError("La nueva aproximación excede la capacidad numérica.")
            f_siguiente = evaluar(funcion, siguiente)
            error_absoluto = abs(siguiente - x_actual)
            if not math.isfinite(error_absoluto):
                raise ValueError("El error entre aproximaciones no es representable.")
        except ValueError as error:
            return _error(
                entrada, error, _codigo_evaluacion(error), "evaluacion_iteracion", filas,
                aproximacion=x_actual, residuo=abs(f_actual),
            )

        error_relativo = None
        if siguiente != 0:
            relativo = abs((siguiente - x_actual) / siguiente) * 100
            if math.isfinite(relativo):
                error_relativo = relativo

        fila = IteracionSecante(
            i=indice,
            x_anterior=x_anterior,
            x_actual=x_actual,
            f_anterior=f_anterior,
            f_actual=f_actual,
            x_siguiente=siguiente,
            f_siguiente=f_siguiente,
            error_absoluto=error_absoluto,
            error_relativo_porcentual=error_relativo,
        )
        filas.append(fila)

        if abs(f_siguiente) <= entrada.tolerancia:
            return _resultado(
                entrada, "EXITO", "La aproximación cumple la tolerancia del residuo.",
                "CONVERGENCIA_RESIDUO", "tolerancia_residuo",
                siguiente, abs(f_siguiente), filas,
            )

        if siguiente == x_actual:
            return _resultado(
                entrada, "ESTANCAMIENTO",
                "La aproximación dejó de cambiar por la precisión numérica, pero el residuo aún supera la tolerancia.",
                "ESTANCAMIENTO", "estancamiento_numerico",
                siguiente, abs(f_siguiente), filas,
            )

        if error_absoluto <= entrada.tolerancia:
            return _resultado(
                entrada, "EXITO",
                "La diferencia entre dos aproximaciones consecutivas cumple la tolerancia.",
                "CONVERGENCIA_POR_ERROR", "error_absoluto",
                siguiente, abs(f_siguiente), filas,
            )

        x_anterior, f_anterior = x_actual, f_actual
        x_actual, f_actual = siguiente, f_siguiente

    ultima = filas[-1]
    return _resultado(
        entrada, "LIMITE_ITERACIONES",
        f"Se alcanzó el límite de {entrada.limite_iteraciones} iteraciones sin cumplir la tolerancia.",
        "LIMITE_ITERACIONES", "limite_iteraciones",
        ultima.x_siguiente, abs(ultima.f_siguiente), filas,
    )


def _validar_entrada(entrada: EntradaSecante) -> EntradaSecante:
    """Normaliza y valida los datos antes de compilar la función."""
    if not isinstance(entrada, EntradaSecante):
        raise ValueError("La entrada debe cumplir el contrato del método de la secante.")

    expresion = validar_expresion(entrada.expresion)
    x_anterior = validar_extremo(entrada.x_anterior, "x₀")
    x_actual = validar_extremo(entrada.x_actual, "x₁")
    if x_anterior == x_actual:
        raise ValueError("Las dos aproximaciones iniciales deben ser diferentes.")

    tolerancia = validar_extremo(entrada.tolerancia, "La tolerancia")
    if tolerancia <= 0:
        raise ValueError("La tolerancia debe ser un número real positivo.")

    limite = validar_limite_iteraciones(entrada.limite_iteraciones)
    unidad = validar_unidad_angular(entrada.unidad_angular)
    return EntradaSecante(
        expresion=expresion,
        x_anterior=x_anterior,
        x_actual=x_actual,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
        unidad_angular=unidad,
    )


def _raiz_inicial(entrada: EntradaSecante, raiz: float) -> ResultadoSecante:
    """Devuelve una aproximación inicial que ya evalúa como cero."""
    return _resultado(
        entrada, "EXITO", "Una de las aproximaciones iniciales ya evalúa como cero.",
        "RAIZ_INICIAL", "raiz_inicial", raiz, 0.0, [],
    )


def _error(
    entrada: EntradaSecante | None,
    error: ValueError,
    codigo: str,
    motivo: str,
    filas: list[IteracionSecante] | None = None,
    *,
    aproximacion: float | None = None,
    residuo: float | None = None,
) -> ResultadoSecante:
    """Construye una salida de error y conserva las iteraciones ya calculadas."""
    return _resultado(
        entrada, "ERROR", str(error), codigo, motivo,
        aproximacion, residuo, filas or [],
    )


def _codigo_evaluacion(error: ValueError) -> str:
    """Conserva el código de dominio si el evaluador lo proporciona."""
    return getattr(error, "codigo", "DOMINIO_INVALIDO")


def _resultado(
    entrada: EntradaSecante | None,
    estado: str,
    mensaje: str,
    codigo: str,
    motivo: str,
    aproximacion: float | None,
    residuo: float | None,
    filas: list[IteracionSecante],
) -> ResultadoSecante:
    """Centraliza la construcción del resultado para mantener coherente la traza."""
    return ResultadoSecante(
        entrada=entrada,
        estado=estado,
        mensaje=mensaje,
        codigo_diagnostico=codigo,
        motivo_parada=motivo,
        aproximacion=aproximacion,
        residuo=residuo,
        iteraciones=tuple(filas),
        iteraciones_totales=len(filas),
    )
