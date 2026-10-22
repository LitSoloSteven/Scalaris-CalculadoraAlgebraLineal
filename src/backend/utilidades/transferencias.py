"""Validación canónica de las cargas internas transferidas entre herramientas."""
from __future__ import annotations

from typing import Any

from src.backend.constantes import MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
from src.backend.utilidades.validadores import ValidadorMatriz


def _envoltura_valida(carga: Any, tipo: str) -> bool:
    claves = {"version", "tipo", "origen", "datos"}
    if tipo == "vectores":
        claves.add("escena")
    return (isinstance(carga, dict) and set(carga) == claves
            and type(carga.get("version")) is int and carga["version"] == 1
            and carga.get("tipo") == tipo and isinstance(carga.get("origen"), str))


def _filas_validas(datos: list, columnas: int) -> bool:
    return all(isinstance(fila, list) and len(fila) == columnas
               and all(ValidadorMatriz.validar_celda(celda) for celda in fila)
               for fila in datos)


def validar_carga_matriz(
    carga: Any, *, dimension_maxima: int
) -> tuple[list[list[str]] | None, str | None]:
    """Devuelve la matriz cuadrada válida y el error, sin transformar sus celdas."""
    if not _envoltura_valida(carga, "matriz_a"):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    datos = carga["datos"]
    if not isinstance(datos, list) or not datos:
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    dimension = len(datos)
    if any(not isinstance(fila, list) or len(fila) != dimension for fila in datos):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    if dimension > dimension_maxima:
        return None, (f"La matriz es de {dimension}×{dimension} y esta herramienta admite hasta "
                      f"{dimension_maxima}×{dimension_maxima}. Empezamos con la herramienta vacía.")
    if not _filas_validas(datos, dimension):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    return datos, None


def _error_dimensiones_sistema(
    filas: int, columnas: int, maximo_ecuaciones: int, dimensiones_permitidas: set[int]
) -> str | None:
    if filas == 0 or filas > maximo_ecuaciones:
        return (f"El sistema debe tener entre 1 y {maximo_ecuaciones} ecuaciones. "
                "Empezamos con la herramienta vacía.")
    if columnas not in dimensiones_permitidas:
        opciones = ", o ".join(map(str, sorted(dimensiones_permitidas)))
        return (f"El sistema tiene {columnas} variables. Esta herramienta solo grafica sistemas "
                f"con {opciones} variables. Empezamos con la herramienta vacía.")
    return None


def _estructura_sistema_valida(coeficientes: Any, independientes: Any) -> bool:
    return (isinstance(coeficientes, list) and isinstance(independientes, list)
            and len(independientes) == len(coeficientes)
            and (not coeficientes or isinstance(coeficientes[0], list)))


def validar_carga_sistema(
    carga: Any, *, maximo_ecuaciones: int, dimensiones_permitidas: set[int]
) -> tuple[dict[str, Any] | None, str | None]:
    """Devuelve los coeficientes y términos válidos con su error, sin calcularlos."""
    if not _envoltura_valida(carga, "sistema"):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    datos = carga["datos"]
    if not isinstance(datos, dict) or set(datos) != {"matriz_a", "vector_b"}:
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    coeficientes, independientes = datos["matriz_a"], datos["vector_b"]
    if not _estructura_sistema_valida(coeficientes, independientes):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    columnas = len(coeficientes[0]) if coeficientes else 0
    error = _error_dimensiones_sistema(
        len(coeficientes), columnas, maximo_ecuaciones, dimensiones_permitidas)
    if error:
        return None, error
    if not _filas_validas(coeficientes, columnas) or not all(
        ValidadorMatriz.validar_celda(celda) for celda in independientes
    ):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    return datos, None


def validar_carga_vectores(
    carga: Any, *, dimensiones_permitidas: set[int]
) -> tuple[dict[str, Any] | None, str | None]:
    """Devuelve escena y vectores válidos con su error, preservando las coordenadas."""
    if not _envoltura_valida(carga, "vectores"):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    datos, escena = carga["datos"], carga["escena"]
    if not isinstance(datos, list) or not datos or not isinstance(datos[0], list):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    if not isinstance(escena, str):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    dimension = len(datos[0])
    if dimension not in dimensiones_permitidas:
        opciones = ", o ".join(map(str, sorted(dimensiones_permitidas)))
        return None, (f"Los vectores tienen dimensión {dimension}. Esta herramienta solo grafica "
                      f"en {opciones}D. Empezamos con la herramienta vacía.")
    if not _filas_validas(datos, dimension):
        return None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
    return {"escena": escena, "vectores": datos}, None
