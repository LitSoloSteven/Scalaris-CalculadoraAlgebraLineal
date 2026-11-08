"""Validacion especifica del contrato de regla falsa sobre entrada cruda."""
import math
from collections.abc import Mapping

from .contrato_regla_falsa import EntradaReglaFalsa
from .limites_raices import LIMITE_ITERACIONES_MAXIMO
from .unidades_angulares import validar_unidad_angular
from .validacion_raices import (
    validar_expresion,
    validar_extremo,
    validar_limite_iteraciones,
)


def validar_entrada_regla_falsa(datos: Mapping[str, object]) -> EntradaReglaFalsa:
    """Valida y devuelve la entrada canonica; lanza ValueError granular."""
    if not isinstance(datos, Mapping):
        raise ValueError("La entrada debe ser un diccionario con la expresion, el intervalo y la tolerancia.")
    expresion = validar_expresion(datos.get("expresion"))
    extremo_izquierdo = validar_extremo(datos.get("extremo_izquierdo"), "extremo_izquierdo")
    extremo_derecho = validar_extremo(datos.get("extremo_derecho"), "extremo_derecho")
    if extremo_izquierdo == extremo_derecho:
        raise ValueError(
            f"El intervalo es invalido: extremo_izquierdo ({extremo_izquierdo}) debe ser menor que extremo_derecho ({extremo_derecho})."
        )
    intercambio = _validar_intercambio(datos.get("intervalo_invertido", False))
    if extremo_izquierdo > extremo_derecho:
        extremo_izquierdo, extremo_derecho = extremo_derecho, extremo_izquierdo
        intercambio = True
    tolerancia = _validar_tolerancia(datos["tolerancia"]) if "tolerancia" in datos else 1e-6
    limite = _validar_limite_regla_falsa(datos["limite_iteraciones"]) if "limite_iteraciones" in datos else 100
    unidad = validar_unidad_angular(datos["unidad_angular"]) if "unidad_angular" in datos else "radianes"
    return EntradaReglaFalsa(
        expresion=expresion,
        extremo_izquierdo=extremo_izquierdo,
        extremo_derecho=extremo_derecho,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
        unidad_angular=unidad,
        intervalo_invertido=intercambio,
    )


def _validar_intercambio(valor: object) -> bool:
    if not isinstance(valor, bool):
        raise ValueError("La marca de intervalo invertido debe ser booleana.")
    return valor


def _validar_tolerancia(valor: object) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError("La tolerancia de residuo debe ser un numero real positivo y finito.")
    try:
        numero = float(valor)
    except OverflowError as error:
        raise ValueError("La tolerancia excede la capacidad numerica.") from error
    if not math.isfinite(numero) or numero <= 0:
        raise ValueError("La tolerancia debe ser positiva, finita y representable.")
    return numero


def _validar_limite_regla_falsa(valor: object) -> int:
    if valor is None:
        raise ValueError(
            f"El limite de iteraciones es obligatorio y debe ser un entero entre 1 y {LIMITE_ITERACIONES_MAXIMO}."
        )
    return validar_limite_iteraciones(valor)