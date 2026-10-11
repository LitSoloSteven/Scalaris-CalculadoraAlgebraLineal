"""Clasificador de operaciones elementales por filas para trazado pedagógico."""
import re
from typing import TypedDict

RE_INICIAL = r"^Matriz inicial"
RE_INTERCAMBIO = r"^Intercambio: Fila (\d+) ↔ Fila (\d+)"
RE_PIVOTE = r"^Pivote seleccionado en Fila (\d+), Columna (\d+)"
RE_ELIMINACION = r"^Fila (\d+) = Fila \1 − \((.+)\) · Fila (\d+)$"
RE_NORMALIZA = r"^Normalizar pivote(?: a 1)?: Fila (\d+) = Fila \1 / (.+)$"


class ParametrosPaso(TypedDict):
    """Estructura de parámetros extraídos de una descripción de paso elemental."""

    kind: str
    row1: int | None
    row2: int | None
    col: int | None
    val_str: str | None


def _construir_resultado_base(tipo: str = "otro") -> ParametrosPaso:
    """Construye un diccionario base para parámetros de paso no inicializados."""
    return {
        "kind": tipo,
        "row1": None,
        "row2": None,
        "col": None,
        "val_str": None,
    }


def clasificar_paso(descripcion: str) -> ParametrosPaso:
    """Identifica el tipo de operación elemental a partir de su texto descriptivo."""
    if re.match(RE_INICIAL, descripcion):
        return _construir_resultado_base("inicial")

    coincidencia = re.match(RE_INTERCAMBIO, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("intercambio")
        resultado["row1"] = int(coincidencia.group(1)) - 1
        resultado["row2"] = int(coincidencia.group(2)) - 1
        return resultado

    coincidencia = re.match(RE_PIVOTE, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("pivote")
        resultado["row1"] = int(coincidencia.group(1)) - 1
        resultado["col"] = int(coincidencia.group(2)) - 1
        return resultado

    coincidencia = re.match(RE_ELIMINACION, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("eliminacion")
        resultado["row1"] = int(coincidencia.group(1)) - 1
        resultado["val_str"] = coincidencia.group(2)
        resultado["row2"] = int(coincidencia.group(3)) - 1
        return resultado

    coincidencia = re.match(RE_NORMALIZA, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("normalizacion")
        resultado["row1"] = int(coincidencia.group(1)) - 1
        resultado["val_str"] = coincidencia.group(2)
        return resultado

    return _construir_resultado_base("otro")
