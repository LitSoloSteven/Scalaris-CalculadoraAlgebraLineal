"""Adaptador puro de los datos del controlador de determinantes al reproductor de pasos."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.backend.models.matrix import Matrix
from src.frontend.components.reproductor_pasos.modelo import (
    GrupoReproductor,
    PasoReproductor,
)


@dataclass(frozen=True)
class CuerpoPasoDeterminante:
    """Contenedor inmutable de los datos de un paso para la vista de determinantes."""

    paso: Mapping[str, Any]
    dimension: int
    total_pasos: int
    metodo: str
    matriz_a: Matrix | None


def recortar_columnas(matriz: Matrix | None, n: int) -> Matrix | None:
    """Devuelve una Matrix con las primeras n columnas si excede el tamaño."""
    if matriz is None or not hasattr(matriz, "rows") or not hasattr(matriz, "cols"):
        return matriz
    if matriz.cols <= n:
        return matriz
    datos_recortados = [
        [matriz.get(i, j) for j in range(n)]
        for i in range(matriz.rows)
    ]
    return Matrix(matriz.rows, n, datos_recortados)


def tipos_leyenda(metodo: str) -> tuple[str, ...]:
    """Devuelve las leyendas asociadas a los tipos de paso según el método."""
    if metodo == "lu":
        return ("inicial", "intercambio", "pivote", "eliminacion", "producto", "singular")
    if metodo == "cofactores":
        return ("planteamiento", "menor", "final")
    return ("operacion",)


def _adaptar_paso(
    paso_dict: Mapping[str, Any],
    posicion: int,
    n: int,
    total_pasos: int,
    contexto: tuple[str, Matrix | None],
) -> PasoReproductor:
    """Convierte un paso del controlador en un PasoReproductor.

    La etiqueta del chip sale del catálogo compartido para mantener tildes y leyenda.
    """
    metodo, matriz_a = contexto
    kind = str(paso_dict.get("kind", "operacion"))
    desc = str(paso_dict.get("description", ""))
    return PasoReproductor(
        indice=int(paso_dict.get("index", posicion)),
        tipo=kind,
        descripcion=desc,
        explicacion=str(paso_dict.get("explanation", desc)),
        indice_grupo=int(paso_dict.get("group_index", 0)),
        cuerpo=CuerpoPasoDeterminante(paso_dict, n, total_pasos, metodo, matriz_a),
        meta_explicar={"kind": kind, "op": desc},
    )


def _adaptar_grupo(g: Mapping[str, Any]) -> GrupoReproductor:
    """Convierte un grupo del controlador al modelo inmutable."""
    return GrupoReproductor(
        titulo=str(g.get("title", "")),
        resumen=str(g.get("summary", "")),
        tipo=str(g.get("kind", "operacion")),
        indices_pasos=tuple(int(i) for i in g.get("step_indices", [])),
    )


def adaptar_pasos_determinante(
    resultado: dict[str, Any],
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte los pasos y grupos del controlador en tuplas para ReproductorPasos."""
    pasos_raw = resultado.get("steps") or []
    if not pasos_raw:
        return (), ()

    contexto = (str(resultado.get("metodo") or ""), resultado.get("matrix_a"))
    n = int(resultado.get("n") or 0)
    pasos = tuple(
        _adaptar_paso(p, i, n, len(pasos_raw), contexto) for i, p in enumerate(pasos_raw)
    )
    grupos = tuple(_adaptar_grupo(g) for g in resultado.get("groups") or [])
    return pasos, grupos