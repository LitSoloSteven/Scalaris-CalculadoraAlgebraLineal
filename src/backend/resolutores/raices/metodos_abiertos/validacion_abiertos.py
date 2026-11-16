"""Validación del contrato de entrada de los métodos abiertos sobre datos crudos."""
from collections.abc import Mapping

from ..validacion_raices import (
    validar_expresion,
    validar_extremo,
    validar_limite_iteraciones,
    validar_tolerancia_positiva,
)
from .contrato_abiertos import EntradaMetodoAbierto, MetodoAbierto

TOLERANCIA_MINIMA = 1e-15
TOLERANCIA_MAXIMA = 1.0
METODOS_ABIERTOS = ("newton", "secante")


def validar_entrada_abierta(datos: Mapping[str, object]) -> EntradaMetodoAbierto:
    """Valida y devuelve la entrada canónica; lanza ValueError con el campo que falla."""
    if not isinstance(datos, Mapping):
        raise ValueError("La entrada debe ser un diccionario con método, expresión y puntos iniciales.")
    metodo = _validar_metodo(datos.get("metodo"))
    expresion = validar_expresion(datos.get("expresion"))
    x0 = validar_extremo(datos.get("x0"), "x0")
    tolerancia = _validar_tolerancia(datos["tolerancia"]) if "tolerancia" in datos else 1e-6
    limite = validar_limite_iteraciones(datos.get("limite_iteraciones"))
    x1 = _validar_segundo_punto(datos.get("x1"), x0) if metodo == "secante" else None
    return EntradaMetodoAbierto(
        metodo=metodo,
        expresion=expresion,
        x0=x0,
        x1=x1,
        tolerancia=tolerancia,
        limite_iteraciones=limite,
    )


def preparar_entrada_abierta(
    entrada: EntradaMetodoAbierto | Mapping[str, object], metodo: MetodoAbierto
) -> EntradaMetodoAbierto:
    """Convierte una captura cruda o revalida la entrada tipada para el método."""
    if isinstance(entrada, Mapping):
        tipada = validar_entrada_abierta(entrada)
    elif isinstance(entrada, EntradaMetodoAbierto):
        tipada = validar_entrada_abierta(_datos_de_entrada(entrada))
    else:
        raise ValueError("La entrada debe ser una captura o una EntradaMetodoAbierto.")
    if tipada.metodo != metodo:
        raise ValueError(f"La entrada debe corresponder al método {metodo}.")
    return tipada


def _datos_de_entrada(entrada: EntradaMetodoAbierto) -> dict[str, object]:
    return {
        "metodo": entrada.metodo,
        "expresion": entrada.expresion,
        "x0": entrada.x0,
        "x1": entrada.x1,
        "tolerancia": entrada.tolerancia,
        "limite_iteraciones": entrada.limite_iteraciones,
    }


def _validar_metodo(valor: object) -> MetodoAbierto:
    if valor not in METODOS_ABIERTOS:
        raise ValueError(
            f"El método debe ser 'newton' o 'secante' (recibido {valor!r})."
        )
    return valor


def _validar_segundo_punto(valor: object, x0: float) -> float:
    if valor is None or valor == "":
        raise ValueError("El segundo punto x1 es obligatorio para el método de la secante.")
    x1 = validar_extremo(valor, "x1")
    if x1 == x0:
        raise ValueError("Los puntos x0 y x1 deben ser distintos para el método de la secante.")
    return x1


def _validar_tolerancia(valor: object) -> float:
    numero = validar_tolerancia_positiva(valor)
    if not TOLERANCIA_MINIMA <= numero <= TOLERANCIA_MAXIMA:
        raise ValueError(
            f"La tolerancia debe ser un número real entre {TOLERANCIA_MINIMA:g} y {TOLERANCIA_MAXIMA:g}."
        )
    return numero
