"""Manejadores atómicos y constructores pedagógicos para pasos de eliminación."""
from dataclasses import dataclass
from typing import Any

from src.backend.utilidades.formateadores import formatear_fraccion_str


@dataclass(frozen=True)
class ContextoPasos:
    """Parámetros de contexto para el procesamiento de pasos de eliminación."""

    contexto: str
    n_izq: int
    es_gauss: bool
    estado_resp: str | None = None


def obtener_valor_pivote(matriz: Any, fila: int, columna: int) -> str:
    """Extrae y formatea el valor fraccionario de una celda de pivote."""
    if matriz is None:
        return ""
    if hasattr(matriz, "obtener"):
        return formatear_fraccion_str(matriz.obtener(fila, columna))
    return formatear_fraccion_str(matriz.get(fila, columna))


def manejar_inicial(
    idx: int,
    ctx: ContextoPasos,
    grupos_crudos: list[dict],
) -> tuple[dict, int]:
    """Genera el grupo y metadatos pedagógicos para la matriz inicial."""
    if ctx.contexto == "inversa":
        explicacion = (
            "Construimos la matriz aumentada [A | I]: A a la izquierda y la "
            "identidad I a la derecha. Meta: aplicar operaciones elementales "
            "de fila hasta obtener [I | A⁻¹]."
        )
        titulo = "Matriz inicial [A | I]"
    elif ctx.es_gauss:
        explicacion = (
            "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
            "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
            "hasta obtener la forma escalonada."
        )
        titulo = "Matriz inicial [A | b]"
    else:
        explicacion = (
            "Escribimos la matriz aumentada [A | b]: los coeficientes a la izquierda "
            "y el vector b a la derecha. Meta: aplicar operaciones elementales de fila "
            "hasta obtener la forma escalonada reducida."
        )
        titulo = "Matriz inicial [A | b]"

    grupos_crudos.append({"kind": "inicial", "title": titulo, "step_indices": [idx]})
    datos_paso = {
        "pivot": None,
        "rows_changed": [],
        "swap_rows": None,
        "explanation": explicacion,
    }
    return datos_paso, len(grupos_crudos) - 1


def manejar_intercambio(
    idx: int,
    parsed: dict,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera el grupo de columna y metadatos pedagógicos para intercambio de filas."""
    f1 = parsed["row1"] + 1
    f2 = parsed["row2"] + 1
    explicacion = (
        f"Intercambiamos la fila {f1} con la fila {f2} para que el pivote "
        f"sea el elemento de mayor valor absoluto de la columna (pivoteo parcial). "
        f"Intercambiar filas no altera el resultado."
    )
    col_group = {
        "kind": "columna",
        "title": "",
        "step_indices": [idx],
        "has_swap": True,
        "pivot_row": None,
        "pivot_col": None,
        "pivot_val": None,
    }
    grupos_crudos.append(col_group)
    estado["col"] = col_group
    datos_paso = {
        "pivot": None,
        "rows_changed": [f1 - 1, f2 - 1],
        "swap_rows": (f1 - 1, f2 - 1),
        "explanation": explicacion,
    }
    return datos_paso, len(grupos_crudos) - 1


def _explicacion_pivote(fila: int, col: int, p_val: str, ctx: ContextoPasos) -> str:
    """Genera la explicación pedagógica del paso de selección de pivote."""
    if ctx.contexto == "inversa":
        return f"Pivote: fila {fila}, columna {col} (valor {p_val}). Usaremos esta fila para anular el resto de la columna {col}."
    if ctx.es_gauss:
        return f"Pivote: fila {fila}, columna {col} (valor {p_val}). Usaremos esta fila para eliminar las entradas debajo del pivote en la columna {col}."
    return f"Pivote: fila {fila}, columna {col} (valor {p_val}). Usaremos esta fila para anular las entradas por encima y por debajo del pivote en la columna {col}."


def _registrar_grupo_pivote(
    idx: int,
    coords: tuple[int, int, str],
    estado_grupos: tuple[list[dict], dict],
) -> int:
    """Actualiza o crea el grupo de columna para el pivote actual."""
    grupos_crudos, estado = estado_grupos
    r, c, p_val = coords
    col_group = estado.get("col")
    if col_group is not None and col_group.get("pivot_row") is None:
        col_group["pivot_row"] = r - 1
        col_group["pivot_col"] = c - 1
        col_group["pivot_val"] = p_val
        col_group["step_indices"].append(idx)
        return grupos_crudos.index(col_group)

    col_group = {
        "kind": "columna",
        "title": "",
        "step_indices": [idx],
        "has_swap": False,
        "pivot_row": r - 1,
        "pivot_col": c - 1,
        "pivot_val": p_val,
    }
    grupos_crudos.append(col_group)
    estado["col"] = col_group
    return len(grupos_crudos) - 1


def manejar_pivote(
    idx: int,
    parsed: dict,
    matriz: Any,
    ctx: ContextoPasos,
    estado_grupos: tuple[list[dict], dict],
) -> tuple[dict, int]:
    """Genera metadatos para la selección de un nuevo pivote."""
    r = parsed["row1"] + 1
    c = parsed["col"] + 1
    p_val = obtener_valor_pivote(matriz, r - 1, c - 1)
    explicacion = _explicacion_pivote(r, c, p_val, ctx)
    grupo_idx = _registrar_grupo_pivote(idx, (r, c, p_val), estado_grupos)
    datos_paso = {
        "pivot": (r - 1, c - 1),
        "rows_changed": [],
        "swap_rows": None,
        "explanation": explicacion,
    }
    return datos_paso, grupo_idx


def _explicacion_eliminacion(t: int, f: str, p: int, col_pivote: int, contexto: str) -> str:
    """Genera la explicación para la operación de eliminación entre filas."""
    if contexto == "inversa":
        return (
            f"Hacemos 0 la entrada de la fila {t} en la columna {col_pivote + 1}: "
            f"Fila {t} = Fila {t} − ({f}) · Fila {p}. La operación afecta la "
            f"fila completa, es decir, los dos bloques a la vez."
        )
    return (
        f"Hacemos 0 la entrada de la fila {t} en la columna {col_pivote + 1}: "
        f"Fila {t} = Fila {t} − ({f}) · Fila {p}. La operación afecta a toda la fila de [A | b]."
    )


def _asociar_grupo_eliminacion(idx: int, grupos_crudos: list[dict], estado: dict) -> int:
    """Asocia el paso de eliminación al grupo de columna o al grupo residual."""
    col_group = estado.get("col")
    if col_group is not None:
        col_group["step_indices"].append(idx)
        return grupos_crudos.index(col_group)
    if estado.get("otro") is None:
        nuevo_otro = {"kind": "otros", "title": "Otras operaciones", "step_indices": [idx]}
        grupos_crudos.append(nuevo_otro)
        estado["otro"] = nuevo_otro
        return len(grupos_crudos) - 1
    estado["otro"]["step_indices"].append(idx)
    return grupos_crudos.index(estado["otro"])


def manejar_eliminacion(
    idx: int,
    parsed: dict,
    ctx: ContextoPasos,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera metadatos para operaciones de anulación por filas."""
    t = parsed["row1"] + 1
    f = parsed["val_str"]
    p = parsed["row2"] + 1
    col_group = estado.get("col")
    col_pivote = col_group["pivot_col"] if (col_group and col_group.get("pivot_col") is not None) else (p - 1)
    explicacion = _explicacion_eliminacion(t, f, p, col_pivote, ctx.contexto)
    grupo_idx = _asociar_grupo_eliminacion(idx, grupos_crudos, estado)
    datos = {
        "pivot": (p - 1, col_pivote),
        "rows_changed": [t - 1],
        "swap_rows": None,
        "explanation": explicacion,
    }
    return datos, grupo_idx


def manejar_normalizacion(
    idx: int,
    parsed: dict,
    ctx: ContextoPasos,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Genera metadatos para operaciones de escalado de pivote a 1."""
    r = parsed["row1"] + 1
    v = parsed["val_str"]
    pivote = (r - 1, r - 1) if (r - 1 < ctx.n_izq) else None
    if ctx.contexto == "inversa":
        explicacion = (
            f"Dividimos la fila {r} entre {v} para que su pivote valga 1 "
            f"y la diagonal del bloque izquierdo quede igual a la identidad."
        )
    else:
        explicacion = f"Dividimos la fila {r} entre {v} para que su pivote valga 1."

    norm_group = estado.get("norm")
    if norm_group is None:
        norm_group = {
            "kind": "normalizacion",
            "title": "Normalización: cada pivote pasa a 1",
            "step_indices": [idx],
        }
        grupos_crudos.append(norm_group)
        estado["norm"] = norm_group
        grupo_idx = len(grupos_crudos) - 1
    else:
        norm_group["step_indices"].append(idx)
        grupo_idx = grupos_crudos.index(norm_group)

    datos = {
        "pivot": pivote,
        "rows_changed": [r - 1],
        "swap_rows": None,
        "explanation": explicacion,
    }
    return datos, grupo_idx


def manejar_otro(
    idx: int,
    descripcion: str,
    grupos_crudos: list[dict],
    estado: dict,
) -> tuple[dict, int]:
    """Asocia pasos no clasificados al grupo activo o a un grupo de operaciones varias."""
    if estado.get("col") is not None:
        estado["col"]["step_indices"].append(idx)
        grupo_idx = grupos_crudos.index(estado["col"])
    elif estado.get("norm") is not None:
        estado["norm"]["step_indices"].append(idx)
        grupo_idx = grupos_crudos.index(estado["norm"])
    elif estado.get("otro") is None:
        nuevo_otro = {"kind": "otros", "title": "Otras operaciones", "step_indices": [idx]}
        grupos_crudos.append(nuevo_otro)
        estado["otro"] = nuevo_otro
        grupo_idx = len(grupos_crudos) - 1
    else:
        estado["otro"]["step_indices"].append(idx)
        grupo_idx = grupos_crudos.index(estado["otro"])

    datos = {
        "pivot": None,
        "rows_changed": [],
        "swap_rows": None,
        "explanation": descripcion,
    }
    return datos, grupo_idx


def construir_titulo_columna(grupo: dict) -> str:
    """Genera el título descriptivo para una etapa de pivoteo por columna."""
    c = grupo.get("pivot_col")
    r = grupo.get("pivot_row")
    val = grupo.get("pivot_val")
    has_swap = grupo.get("has_swap", False)
    if c is not None and r is not None and val is not None:
        titulo = f"Columna {c + 1} · pivote {val} en fila {r + 1}"
        if has_swap:
            titulo += " · con intercambio"
        return titulo
    if c is not None:
        return f"Columna {c + 1}"
    return "Columna"
