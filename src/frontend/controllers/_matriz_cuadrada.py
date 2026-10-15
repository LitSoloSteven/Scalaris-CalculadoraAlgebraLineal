"""Validación y parseo exacto de matrices cuadradas desde payloads del frontend."""
from __future__ import annotations

from fractions import Fraction
from typing import Any

from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator


def _construir_error(
    mensaje: str,
    n: int = 0,
    celda_error: list[int] | None = None,
) -> tuple[None, dict[str, Any]]:
    """Construye la tupla de error estructurada para el controlador."""
    return None, {
        "message": mensaje,
        "n": n,
        "error_cell": celda_error,
    }


def _validar_dimension(valor_n: Any, max_n: int) -> tuple[int | None, str | None]:
    """Verifica que n sea un entero estricto dentro del rango [1, max_n]."""
    if isinstance(valor_n, bool) or not isinstance(valor_n, int):
        return (
            None,
            "La dimensión debe ser un número entero. Revisa el tamaño de la matriz.",
        )
    if valor_n < 1 or valor_n > max_n:
        return (
            None,
            f"La dimensión debe estar entre 1 y {max_n} (recibido {valor_n}×{valor_n}). "
            f"Ajusta el tamaño e inténtalo de nuevo.",
        )
    return valor_n, None


def _parsear_celdas(
    filas_crudas: Any,
    n: int,
) -> tuple[list[list[Fraction]] | None, dict[str, Any] | None]:
    """Valida la forma cuadrada n×n y convierte cada celda a Fraction exacto."""
    if not isinstance(filas_crudas, list) or len(filas_crudas) != n:
        return _construir_error(
            f"Se esperaban {n} filas en la matriz. Revisa los datos de entrada.",
            n=n,
        )

    datos_exactos: list[list[Fraction]] = []
    for indice_fila, fila in enumerate(filas_crudas):
        if not isinstance(fila, list) or len(fila) != n:
            return _construir_error(
                f"La fila {indice_fila + 1} debe tener {n} columnas. "
                f"Completa la cuadrícula e inténtalo de nuevo.",
                n=n,
            )
        fila_exacta: list[Fraction] = []
        for indice_col, valor_celda in enumerate(fila):
            texto_celda = (
                "0"
                if valor_celda is None or str(valor_celda).strip() == ""
                else str(valor_celda).strip()
            )
            exito, fraccion, motivo = MatrixValidator.parse_number_exact(texto_celda)
            if not exito:
                return _construir_error(
                    f"Error en A[{indice_fila + 1},{indice_col + 1}]: {motivo}",
                    n=n,
                    celda_error=[indice_fila, indice_col],
                )
            fila_exacta.append(fraccion)
        datos_exactos.append(fila_exacta)

    return datos_exactos, None


def parsear_matriz_cuadrada(
    datos: dict[str, Any],
    *,
    max_n: int,
) -> tuple[Matrix | None, dict[str, Any] | None]:
    """Parsea un diccionario con 'n' y 'data' en una instancia exacta de Matrix."""
    if not isinstance(datos, dict):
        return _construir_error(
            "Los datos de la matriz no tienen un formato válido. Inténtalo de nuevo."
        )

    n_valido, error_dim = _validar_dimension(datos.get("n"), max_n)
    if error_dim is not None or n_valido is None:
        n_reporte = datos.get("n") if isinstance(datos.get("n"), int) and not isinstance(datos.get("n"), bool) else 0
        return _construir_error(error_dim or "Dimensión inválida.", n=n_reporte)

    datos_exactos, error_celdas = _parsear_celdas(datos.get("data"), n_valido)
    if error_celdas is not None or datos_exactos is None:
        return None, error_celdas

    try:
        return Matrix(n_valido, n_valido, datos_exactos), None
    except MatrixDataError as exc:
        return _construir_error(str(exc), n=n_valido)