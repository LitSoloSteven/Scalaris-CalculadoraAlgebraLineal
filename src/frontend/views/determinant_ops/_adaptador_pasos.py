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


def adaptar_pasos_determinante(
    resultado: dict[str, Any],
) -> tuple[tuple[PasoReproductor, ...], tuple[GrupoReproductor, ...]]:
    """Convierte los pasos y grupos del controlador en tuplas para ReproductorPasos."""
    steps_raw = resultado.get("steps") or []
    groups_raw = resultado.get("groups") or []
    metodo = str(resultado.get("metodo") or "")
    n = int(resultado.get("n") or 0)
    matriz_a = resultado.get("matrix_a")

    if not steps_raw:
        return (), ()

    total_pasos = len(steps_raw)
    pasos: list[PasoReproductor] = []

    for paso_dict in steps_raw:
        idx = int(paso_dict.get("index", len(pasos)))
        kind = str(paso_dict.get("kind", "operacion"))
        desc = str(paso_dict.get("description", ""))
        expl = str(paso_dict.get("explanation", desc))
        grp_idx = int(paso_dict.get("group_index", 0))

        cuerpo = CuerpoPasoDeterminante(
            paso=paso_dict,
            dimension=n,
            total_pasos=total_pasos,
            metodo=metodo,
            matriz_a=matriz_a,
        )
        meta = {"kind": kind, "op": desc}

        pasos.append(
            PasoReproductor(
                indice=idx,
                tipo=kind,
                etiqueta_tipo=kind.capitalize(),
                descripcion=desc,
                explicacion=expl,
                indice_grupo=grp_idx,
                cuerpo=cuerpo,
                meta_explicar=meta,
            )
        )

    grupos: list[GrupoReproductor] = []
    for g in groups_raw:
        titulo = str(g.get("title", ""))
        resumen = str(g.get("summary", ""))
        g_kind = str(g.get("kind", "operacion"))
        step_indices = tuple(int(i) for i in g.get("step_indices", []))

        grupos.append(
            GrupoReproductor(
                titulo=titulo,
                resumen=resumen,
                tipo=g_kind,
                indices_pasos=step_indices,
            )
        )

    return tuple(pasos), tuple(grupos)