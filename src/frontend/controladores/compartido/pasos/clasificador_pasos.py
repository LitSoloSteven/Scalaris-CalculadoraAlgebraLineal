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

    tipo: str
    fila_origen: int | None
    fila_destino: int | None
    columna: int | None
    texto_valor: str | None


def _construir_resultado_base(tipo: str = "otro") -> ParametrosPaso:
    """Construye un diccionario base para parámetros de paso no inicializados."""
    return {
        "tipo": tipo,
        "fila_origen": None,
        "fila_destino": None,
        "columna": None,
        "texto_valor": None,
    }


def clasificar_paso(descripcion: str) -> ParametrosPaso:
    """Identifica el tipo de operación elemental a partir de su texto descriptivo."""
    if re.match(RE_INICIAL, descripcion):
        return _construir_resultado_base("inicial")

    coincidencia = re.match(RE_INTERCAMBIO, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("intercambio")
        resultado["fila_origen"] = int(coincidencia.group(1)) - 1
        resultado["fila_destino"] = int(coincidencia.group(2)) - 1
        return resultado

    coincidencia = re.match(RE_PIVOTE, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("pivote")
        resultado["fila_origen"] = int(coincidencia.group(1)) - 1
        resultado["columna"] = int(coincidencia.group(2)) - 1
        return resultado

    coincidencia = re.match(RE_ELIMINACION, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("eliminacion")
        resultado["fila_origen"] = int(coincidencia.group(1)) - 1
        resultado["texto_valor"] = coincidencia.group(2)
        resultado["fila_destino"] = int(coincidencia.group(3)) - 1
        return resultado

    coincidencia = re.match(RE_NORMALIZA, descripcion)
    if coincidencia:
        resultado = _construir_resultado_base("normalizacion")
        resultado["fila_origen"] = int(coincidencia.group(1)) - 1
        resultado["texto_valor"] = coincidencia.group(2)
        return resultado

    return _construir_resultado_base("otro")
