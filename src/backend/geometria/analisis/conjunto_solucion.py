"""Clasificación y representación analítica del conjunto solución en geometría."""
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any


class TipoSolucionGeometria(str, Enum):
    """Tipos geométricos del conjunto solución de un sistema lineal."""

    VACIA = "VACIA"
    PUNTO = "PUNTO"
    RECTA = "RECTA"
    PLANO = "PLANO"
    ESPACIO_AFIN = "ESPACIO_AFIN"


@dataclass(frozen=True)
class ConjuntoSolucion:
    """Representación del conjunto solución geométrico con aritmética exacta."""

    tipo: TipoSolucionGeometria
    dimension: int
    punto: tuple[Fraction, ...] | None
    direcciones: tuple[tuple[Fraction, ...], ...]

def clasificar_conjunto_solucion(
    punto: tuple[Fraction, ...] | None,
    direcciones: tuple[tuple[Fraction, ...], ...],
) -> TipoSolucionGeometria:
    """Clasifica el conjunto solución según punto y cantidad de direcciones."""
    if punto is None:
        return TipoSolucionGeometria.VACIA
    cantidad_direcciones = len(direcciones)
    if cantidad_direcciones == 0:
        return TipoSolucionGeometria.PUNTO
    if cantidad_direcciones == 1:
        return TipoSolucionGeometria.RECTA
    if cantidad_direcciones == 2:
        return TipoSolucionGeometria.PLANO
    return TipoSolucionGeometria.ESPACIO_AFIN


def tiene_parametros_solucion(resultado: dict[str, Any]) -> bool:
    """Verifica si el diccionario contiene parámetros de solución infinitas."""
    return resultado.get("parametros_solucion") is not None


def obtener_parametros_solucion(resultado: dict[str, Any]) -> dict | None:
    """Extrae y valida la estructura y tipos de los parámetros de solución."""
    parametros = resultado.get("parametros_solucion")
    if parametros is None:
        return None
    try:
        campos = (
            parametros["numero_variables"], parametros["particular"], parametros["direcciones"],
            parametros["columnas_libres"], parametros["nombres_parametros"],
        )
        if not _dimensiones_parametros_coinciden(campos):
            return None
        if not _coeficientes_parametros_son_exactos(campos[1], campos[2]):
            return None
        return parametros
    except (KeyError, TypeError, ValueError):
        return None


def _dimensiones_parametros_coinciden(campos: tuple) -> bool:
    cantidad_variables, particular, direcciones, libres, nombres = campos
    return not (
        cantidad_variables != len(particular)
        or len(direcciones) != len(libres)
        or len(libres) != len(nombres)
    )


def _coeficientes_parametros_son_exactos(particular: list, direcciones: list) -> bool:
    if any(not isinstance(valor, Fraction) for valor in particular):
        return False
    for direccion in direcciones:
        if any(not isinstance(valor, Fraction) for valor in direccion):
            return False
    return True


def construir_conjunto_desde_parametros(
    parametros: dict[str, Any] | None,
) -> ConjuntoSolucion | None:
    """Instancia un ConjuntoSolucion a partir del diccionario de parámetros."""
    if parametros is None:
        return None
    punto = tuple(parametros["particular"])
    direcciones = tuple(tuple(direccion) for direccion in parametros["direcciones"])
    tipo = clasificar_conjunto_solucion(punto, direcciones)
    return ConjuntoSolucion(
        tipo=tipo,
        dimension=len(direcciones),
        punto=punto,
        direcciones=direcciones,
    )


def construir_conjunto_desde_gauss(
    resultado: dict[str, Any],
) -> ConjuntoSolucion | None:
    """Construye el conjunto solución a partir del resultado del resolutor Gauss."""
    estado = resultado.get("estado")
    if estado == "SIN_SOLUCION":
        return ConjuntoSolucion(
            tipo=TipoSolucionGeometria.VACIA,
            dimension=0,
            punto=None,
            direcciones=(),
        )
    if estado == "SOLUCION_UNICA":
        sol_exacta = resultado.get("solucion_exacta") or []
        punto = tuple(Fraction(valor_solucion) for valor_solucion in sol_exacta)
        return ConjuntoSolucion(
            tipo=TipoSolucionGeometria.PUNTO,
            dimension=0,
            punto=punto,
            direcciones=(),
        )
    if estado == "SOLUCIONES_INFINITAS":
        parametros = obtener_parametros_solucion(resultado)
        if parametros is not None:
            return construir_conjunto_desde_parametros(parametros)
    return None


def validar_solucion_parametrica(
    filas_coef: list[list[Fraction]],
    terminos_indep: list[Fraction],
    particular: list[Fraction],
    direcciones: list[list[Fraction]],
) -> bool:
    """Verifica defensivamente que A · p = b y A · d_k = 0 para toda dirección."""
    for fila, b_esperado in zip(filas_coef, terminos_indep):
        valor_p = sum(coeficiente * valor_particular for coeficiente, valor_particular in zip(fila, particular))
        if valor_p != b_esperado:
            return False
        for direccion in direcciones:
            valor_d = sum(coeficiente * valor_direccion for coeficiente, valor_direccion in zip(fila, direccion))
            if valor_d != 0:
                return False
    return True
