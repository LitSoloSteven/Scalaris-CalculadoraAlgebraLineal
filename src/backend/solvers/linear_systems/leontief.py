"""Modelo de Leontief (insumo-producto) resuelto como sistema lineal.

El modelo de Leontief plantea:
    x = A·x + d

donde:
    A : matriz n×n de coeficientes técnicos (a_{ij} = insumo del sector i
        por unidad producida del sector j).
    d : vector n×1 de demanda final.
    x : vector n×1 de producción total (la incógnita).

Reordenando:
    (I − A)·x = d

Este solver reutiliza GaussSolver: construye [I − A | d], lo resuelve con
eliminación exacta, y devuelve la producción x + verificación (I−A)·x = d
+ interpretación económica en castellano.

No se delega en ninguna biblioteca de álgebra lineal. Solo stdlib + Fraction.

Notas para el partner de Frontend:
    El contrato incluye `sector_names` como campo OPCIONAL. Si no se pasa,
    el solver genera por defecto ["x_1", "x_2", ..., "x_n"]. La vista puede
    usar esos nombres para etiquetar la interpretación (y el texto de
    `interpretation` ya los incorpora en el formato "nombre = valor").
    Si en algún momento se decide eliminar esta funcionalidad, es seguro
    hacerlo: nada más depende de ella y los tests de sector_names se
    pueden borrar sin afectar al resto del contrato.
"""
from __future__ import annotations

from fractions import Fraction

from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.gauss import GaussSolver
from src.backend.solvers.matrix_ops.formatters import (
    matrix_to_latex,
    partitioned_matrix_to_latex,
)
from src.backend.solvers.matrix_ops.operations import MatrixOpsSolver
from src.backend.solvers.vector_ops.formatters import vector_to_latex
from src.backend.utils.formatters import format_fraction_str


def solve_leontief(
    A: Matrix,
    d: Matrix,
    sector_names: list[str] | None = None,
) -> dict:
    """Resuelve el modelo de Leontief (I − A)·x = d.

    Args:
        A: Matriz cuadrada n×n de coeficientes técnicos.
        d: Vector columna n×1 de demanda final.
        sector_names: Lista opcional de n nombres de sector. Si no se pasa,
            se generan por defecto ["x_1", ..., "x_n"].

    Returns:
        dict con el contrato documentado en el docstring del módulo.
    """
    # --- Validaciones tempranas ---
    if not isinstance(A, Matrix):
        return _error("Se esperaba una Matrix para A.")
    if not isinstance(d, Matrix):
        return _error("Se esperaba una Matrix para d.")
    if A.rows != A.cols:
        return _error(
            f"A debe ser cuadrada (coeficientes técnicos); "
            f"recibido {A.rows}×{A.cols}."
        )
    n = A.rows
    if d.rows != n or d.cols != 1:
        return _error(
            f"d debe ser un vector columna {n}×1; "
            f"recibido {d.rows}×{d.cols}."
        )
    if sector_names is not None:
        if not isinstance(sector_names, list):
            return _error("sector_names debe ser una lista.")
        if len(sector_names) != n:
            return _error(
                f"sector_names tiene {len(sector_names)} nombres; "
                f"se esperaban {n} (uno por sector)."
            )
        for name in sector_names:
            if not isinstance(name, str):
                return _error("Todos los sector_names deben ser strings.")

    names = (
        list(sector_names)
        if sector_names is not None
        else [f"x_{i + 1}" for i in range(n)]
    )

    # --- Construir I − A ---
    ima_data: list[list[Fraction]] = []
    for i in range(n):
        row: list[Fraction] = []
        for j in range(n):
            delta = Fraction(1) if i == j else Fraction(0)
            row.append(delta - Fraction(A.get(i, j)))
        ima_data.append(row)
    I_minus_A = Matrix(n, n, ima_data)

    # --- Construir [I − A | d] ---
    aug_data: list[list[Fraction]] = []
    for i in range(n):
        row = [I_minus_A.get(i, j) for j in range(n)]
        row.append(Fraction(d.get(i, 0)))
        aug_data.append(row)
    augmented = Matrix(n, n + 1, aug_data)

    # --- Resolver con GaussSolver (fuente única de eliminación exacta) ---
    gauss_result = GaussSolver(augmented).solve()
    status = gauss_result["status"]

    # --- Traza: planteamiento [I − A | d] + pasos de Gauss ---
    # El primer paso de Gauss ("Matriz inicial aumentada [A|b]:") es
    # redundante con nuestro paso de planteamiento, así que lo descartamos.
    steps: list[dict] = [{
        "description": (
            "Sistema (I − A)·x = d planteado como matriz aumentada [I − A | d]:"
        ),
        "matrix": augmented,
        "detail_latex": partitioned_matrix_to_latex(augmented, n),
    }]
    raw_gauss_steps = gauss_result.get("steps", [])
    if raw_gauss_steps and "Matriz inicial aumentada" in raw_gauss_steps[0]["description"]:
        raw_gauss_steps = raw_gauss_steps[1:]
    for step in raw_gauss_steps:
        mat = step.get("matrix")
        steps.append({
            "description": step["description"],
            "matrix": mat,
            "detail_latex": (
                partitioned_matrix_to_latex(mat, n)
                if mat is not None
                else None
            ),
        })

    ima_latex = matrix_to_latex(I_minus_A)
    d_latex = vector_to_latex(d)

    # GaussSolver devuelve "UNIQUE_SOLUTION" para el caso determinado.
    # Nuestro contrato expone "SUCCESS" (consistente con LUFactorizationSolver
    # y determinants). Los demás estados se propagan sin cambio.
    status_out = "SUCCESS" if status == "UNIQUE_SOLUTION" else status

    base = {
        "status": status_out,
        "message": "",
        "A": A,
        "d": d,
        "sector_names": names,
        "I_minus_A": I_minus_A,
        "I_minus_A_latex": ima_latex,
        "d_latex": d_latex,
        "x": None,
        "x_latex": None,
        "solution": None,
        "solution_param": None,
        "steps": steps,
        "verification": None,
        "interpretation": "",
        "error_cell": None,
    }

    # --- Clasificación ---
    if status == "NO_SOLUTION":
        base["message"] = (
            "El sistema (I − A)·x = d es inconsistente: no existe un vector "
            "de producción que satisfaga exactamente la demanda final."
        )
        base["interpretation"] = (
            "El sistema (I − A)·x = d es inconsistente. En términos del modelo "
            "de Leontief, la matriz de coeficientes técnicos A y la demanda "
            "final d no son compatibles: no existe un vector de producción x "
            "que abastezca exactamente la demanda sin déficits. La matriz A no "
            "es productiva con estos datos."
        )
        return base

    if status == "INFINITE_SOLUTIONS":
        base["message"] = (
            "El sistema (I − A)·x = d admite infinitas soluciones: "
            "(I − A) tiene rango deficiente."
        )
        base["solution"] = gauss_result.get("solution")
        base["solution_param"] = gauss_result.get("solution_param")
        base["interpretation"] = (
            "El sistema (I − A)·x = d admite infinitas soluciones porque la "
            "matriz (I − A) tiene rango deficiente. El modelo está "
            "subdeterminado: existen múltiples vectores de producción x que "
            "satisfacen la demanda final. Se necesita información adicional "
            "(por ejemplo, fijar la producción de algunos sectores) para "
            "obtener una solución única."
        )
        return base

    # --- SUCCESS (UNIQUE_SOLUTION) ---
    x_exact: list[Fraction] = list(gauss_result.get("solution_exact") or [])
    x_matrix = Matrix(n, 1, [[v] for v in x_exact])
    x_latex = vector_to_latex(x_matrix)

    # Verificación (I − A)·x == d, reutilizando MatrixOpsSolver.
    ops = MatrixOpsSolver()
    product = ops.multiply(I_minus_A, x_matrix)["result_matrix"]
    coincide = all(
        Fraction(product.get(i, 0)) == Fraction(d.get(i, 0))
        for i in range(n)
    )
    status_word = "Correcto" if coincide else "Incorrecto"
    verification = {
        "coincide": coincide,
        "product": product,
        "detail_latex": (
            f"(I - A) \\cdot x = {matrix_to_latex(product)}"
            f" \\quad (\\text{{{status_word}}})"
        ),
    }

    products_str = ", ".join(
        f"{name} = {format_fraction_str(v)}"
        for name, v in zip(names, x_exact)
    )

    base["message"] = (
        f"Sistema (I − A)·x = d resuelto: {n} sectores, solución única."
    )
    base["x"] = x_exact
    base["x_latex"] = x_latex
    base["verification"] = verification
    base["interpretation"] = (
        f"Con la matriz de coeficientes técnicos A y la demanda final d, "
        f"el modelo de Leontief plantea x = A·x + d. Reordenando: (I − A)·x = d. "
        f"La solución {products_str} es la producción total que cada sector "
        f"debe generar para satisfacer exactamente la demanda final: ni más "
        f"(excedentes que sobran) ni menos (faltantes que no se cubren)."
    )
    return base


def _error(message: str) -> dict:
    """Construye un resultado vacío homogéneo para errores de validación."""
    return {
        "status": "ERROR",
        "message": message,
        "A": None,
        "d": None,
        "sector_names": [],
        "I_minus_A": None,
        "I_minus_A_latex": None,
        "d_latex": None,
        "x": None,
        "x_latex": None,
        "solution": None,
        "solution_param": None,
        "steps": [],
        "verification": None,
        "interpretation": "",
        "error_cell": None,
    }