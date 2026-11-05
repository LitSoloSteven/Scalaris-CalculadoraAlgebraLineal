"""Operaciones reales con errores de dominio y capacidad numérica controlados."""
import ast
import math
from collections.abc import Callable

from src.backend.excepciones import ErrorDominio, ErrorNoFinito
from .errores_numericos import ErrorCapacidadNumerica
from .gramatica_funcion import FUNCIONES_REALES
from .unidades_angulares import argumento_angular, resultado_angular, validar_unidad_angular

_OPERACIONES = {ast.Add: lambda izquierda, derecha: izquierda + derecha,
                ast.Sub: lambda izquierda, derecha: izquierda - derecha,
                ast.Mult: lambda izquierda, derecha: izquierda * derecha,
                ast.Div: lambda izquierda, derecha: izquierda / derecha,
                ast.Pow: lambda izquierda, derecha: izquierda ** derecha}


def comprobar_real(valor: object) -> float:
    """Devuelve un número real finito; lanza ErrorDominio o ErrorNoFinito."""
    if type(valor) not in (int, float):
        raise ErrorDominio("La función no es real en un punto del intervalo.")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ErrorCapacidadNumerica("El valor excede la capacidad numérica.") from error
    if not math.isfinite(numero):
        raise ErrorCapacidadNumerica("La evaluación produjo un valor no finito.")
    return numero


def aplicar_operador(operador: ast.operator, izquierda: float, derecha: float) -> float:
    """Aplica un operador permitido; traduce fallos y detecta ceros por subdesbordamiento."""
    operacion = _OPERACIONES.get(type(operador))
    if operacion is None:
        raise ValueError("Operador no permitido.")
    resultado = ejecutar_operacion(lambda: operacion(izquierda, derecha))
    producto_no_nulo = isinstance(operador, ast.Mult) and izquierda != 0 and derecha != 0
    cociente_o_potencia = isinstance(operador, (ast.Div, ast.Pow)) and izquierda != 0
    _comprobar_subdesbordamiento(resultado, producto_no_nulo or cociente_o_potencia)
    return resultado


def aplicar_funcion(nombre: str, argumento: float, *, unidad_angular: str = "radianes") -> float:
    """Evalúa una función real de un argumento y detecta la pérdida total de exp."""
    unidad = validar_unidad_angular(unidad_angular)
    argumento = argumento_angular(nombre, comprobar_real(argumento), unidad)
    resultado = ejecutar_operacion(lambda: FUNCIONES_REALES[nombre](argumento))
    _comprobar_subdesbordamiento(resultado, nombre == "exp")
    return comprobar_real(resultado_angular(nombre, resultado, unidad))


def ejecutar_operacion(operacion: Callable[[], float]) -> float:
    """Traduce las excepciones numéricas de Python al contrato castellano del evaluador."""
    try:
        return comprobar_real(operacion())
    except ZeroDivisionError as error:
        raise ErrorDominio("División por cero en la función.") from error
    except OverflowError as error:
        raise ErrorCapacidadNumerica("Desbordamiento numérico al evaluar la función.") from error
    except (TypeError, ValueError) as error:
        if isinstance(error, (ErrorDominio, ErrorNoFinito)):
            raise
        raise ErrorDominio("La función no es real en un punto del intervalo.") from error


def _comprobar_subdesbordamiento(resultado: float, matematicamente_no_nulo: bool) -> None:
    if resultado == 0 and matematicamente_no_nulo:
        raise ErrorCapacidadNumerica("La evaluación se redondea a cero por subdesbordamiento.", "SUBDESBORDAMIENTO")
