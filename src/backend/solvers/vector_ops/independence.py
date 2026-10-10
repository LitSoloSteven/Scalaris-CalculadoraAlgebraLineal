"""Prueba de independencia lineal de un conjunto de vectores.

Dados v_1, ..., v_k ∈ R^n, son linealmente independientes si y solo si
el sistema homogéneo [v_1 | ... | v_k] · c = 0 admite únicamente la
solución trivial c = 0. Este solver reutiliza solve_homogeneous del
módulo linear_systems y agrega:

  - La semántica de vectores (INDEPENDENT / DEPENDENT en lugar de
    TRIVIAL_ONLY / NON_TRIVIAL).
  - Una lista de relaciones de dependencia explícitas para el caso LD.
    Cada dirección del kernel c = (c_1, ..., c_k) da lugar a la
    combinación c_1·v_1 + ... + c_k·v_k = 0, que se formatea en LaTeX y
    en texto plano para mostrar en la exposición.
  - Una explicación en castellano que menciona rank, k y n.

No se modifica ningún otro solver ni se duplica eliminación.
"""
from __future__ import annotations

from fractions import Fraction

from src.backend.exceptions import InvalidVectorError
from src.backend.models.matrix import Matrix
from src.backend.solvers.linear_systems.homogeneous import solve_homogeneous
from src.backend.solvers.matrix_ops.formatters import matrix_to_latex
from src.backend.utils.formatters import format_fraction_str


# =========================================================================
# API pública
# =========================================================================

def test_independence(vectors: list[Matrix]) -> dict:
    """Decide si {vectors} es linealmente independiente.

    Args:
        vectors: lista de Matrix columna n×1, todas con la misma n.

    Returns:
        dict con:
          - status: INDEPENDENT | DEPENDENT | ERROR
          - message: resumen en castellano
          - is_independent: bool (True ⇔ INDEPENDENT)
          - rank: rango de [v_1 | ... | v_k]
          - num_vectors: k
          - dim: n
          - pivot_cols, free_cols: pivotes y variables libres del sistema
          - dependency_relations: [] si INDEPENDENT; lista de dicts
            {coefficients, relation_latex, relation_plain} si DEPENDENT
          - reduced_matrix: A reducida por filas (n×k)
          - steps: pasos de la eliminación
          - explanation: str en castellano listo para mostrar
          - error_cell: None
    """
    # --- 1. Validación ---
    if not isinstance(vectors, list):
        return _empty_result("ERROR", "Se esperaba una lista de vectores.")
    if len(vectors) == 0:
        return _empty_result("ERROR", "Se requiere al menos un vector.")

    for i, v in enumerate(vectors):
        if not isinstance(v, Matrix):
            return _empty_result(
                "ERROR",
                f"El elemento {i + 1} no es una Matrix.",
            )
        if v.cols != 1:
            return _empty_result(
                "ERROR",
                f"v_{i + 1}: se esperaba vector columna n×1, "
                f"recibido {v.rows}×{v.cols}.",
            )

    n = vectors[0].rows
    for i, v in enumerate(vectors):
        if v.rows != n:
            return _empty_result(
                "ERROR",
                f"Dimensiones incompatibles: v_1 tiene dim {n}, "
                f"v_{i + 1} tiene dim {v.rows}.",
            )

    k = len(vectors)

    # --- 2. Construir A = [v_1 | ... | v_k] (n × k) ---
    data = [
        [vectors[j].get(i, 0) for j in range(k)]
        for i in range(n)
    ]
    matrix_a = Matrix(n, k, data)

    # --- 3. Resolver el sistema homogéneo A·c = 0 ---
    homo = solve_homogeneous(matrix_a)

    # --- 4. Mapear a la semántica de independencia ---
    rank = homo["rank"]
    free_cols = homo["free_cols"]
    pivot_cols = homo["pivot_cols"]
    reduced = homo["reduced_matrix"]
    steps = homo["steps"]

    if homo["status"] == "TRIVIAL_ONLY":
        return {
            "status": "INDEPENDENT",
            "message": (
                f"Los {k} vectores son linealmente independientes "
                f"(rank = {rank} = k = {k})."
            ),
            "is_independent": True,
            "rank": rank,
            "num_vectors": k,
            "dim": n,
            "pivot_cols": pivot_cols,
            "free_cols": [],
            "dependency_relations": [],
            "reduced_matrix": reduced,
            "steps": steps,
            "explanation": (
                f"El sistema homogéneo [v_1 | ... | v_{k}] · c = 0 tiene "
                f"únicamente la solución trivial c = 0 (rank = {rank} = "
                f"k = {k}). Por lo tanto los {k} vectores son linealmente "
                f"independientes. Ningún vector del conjunto es combinación "
                f"lineal de los demás."
            ),
            "error_cell": None,
        }

    # DEPENDENT
    sp = homo["solution_param"]
    relations = _build_dependency_relations(
        sp=sp,
        vectors=vectors,
        k=k,
    )

    return {
        "status": "DEPENDENT",
        "message": (
            f"Los {k} vectores son linealmente dependientes "
            f"(rank = {rank} < k = {k})."
        ),
        "is_independent": False,
        "rank": rank,
        "num_vectors": k,
        "dim": n,
        "pivot_cols": pivot_cols,
        "free_cols": free_cols,
        "dependency_relations": relations,
        "reduced_matrix": reduced,
        "steps": steps,
        "explanation": (
            f"El sistema homogéneo [v_1 | ... | v_{k}] · c = 0 admite "
            f"soluciones no triviales (rank = {rank} < k = {k}). Por lo "
            f"tanto los {k} vectores son linealmente dependientes: existe "
            f"al menos una combinación lineal con coeficientes no todos "
            f"nulos que da el vector cero."
        ),
        "error_cell": None,
    }

# Pytest recolecta cualquier función cuyo nombre empiece con 'test_' que
# encuentre en el namespace de un módulo de tests, incluidas las
# importadas. La función pública de este módulo se llama 'test_independence'
# por semántica de dominio (es la prueba de independencia lineal), no
# porque sea un test. Este atributo le dice a pytest que la salte.
test_independence.__test__ = False

# =========================================================================
# Helpers
# =========================================================================

def _empty_result(status: str, message: str) -> dict:
    return {
        "status": status,
        "message": message,
        "is_independent": False,
        "rank": None,
        "num_vectors": 0,
        "dim": 0,
        "pivot_cols": [],
        "free_cols": [],
        "dependency_relations": [],
        "reduced_matrix": None,
        "steps": [],
        "explanation": "",
        "error_cell": None,
    }


def _build_dependency_relations(
    *,
    sp: dict | None,
    vectors: list[Matrix],
    k: int,
) -> list[dict]:
    """Construye la relación c_1·v_1 + ... + c_k·v_k = 0 para cada
    dirección del kernel del sistema homogéneo."""
    if not sp:
        return []

    relations = []
    for d in sp["directions"]:
        coeffs = [Fraction(c) for c in d]
        # Ignorar direcciones triviales (todas las componentes cero).
        if all(c == 0 for c in coeffs):
            continue
        relation = {
            "coefficients": coeffs,
            "relation_latex": _build_relation_latex(coeffs),
            "relation_plain": _build_relation_plain(coeffs),
        }
        relations.append(relation)
    return relations


def _build_relation_latex(coeffs: list[Fraction]) -> str:
    """Formatea Σ c_i · v_i = 0 en LaTeX con signos correctos."""
    parts = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        v_tex = f"v_{{{i + 1}}}"
        if c == 1:
            term = v_tex
        elif c == -1:
            term = f"-{v_tex}"
        else:
            coeff_str = format_fraction_str(c)
            if c < 0:
                # Para signos negativos: -(|c|) v_i
                abs_c = abs(c)
                abs_str = format_fraction_str(abs_c)
                term = f"-\\left({abs_str}\\right) {v_tex}" if abs_c.denominator != 1 \
                    else f"-{abs_str} {v_tex}"
            else:
                term = f"{coeff_str} {v_tex}" if c.denominator != 1 \
                    else f"{coeff_str} {v_tex}"

        if not parts:
            parts.append(term)
        else:
            if c > 0:
                parts.append(f"+ {term}")
            else:
                # term ya trae el guion
                parts.append(term)

    if not parts:
        return r"0 = 0"

    return " ".join(parts) + " = \\mathbf{0}"


def _build_relation_plain(coeffs: list[Fraction]) -> str:
    """Formatea Σ c_i · v_i = 0 en texto plano."""
    parts = []
    for i, c in enumerate(coeffs):
        if c == 0:
            continue
        v_name = f"v_{i + 1}"
        c_str = format_fraction_str(c)
        if c == 1:
            term = v_name
        elif c == -1:
            term = f"-{v_name}"
        else:
            # Envuelve fracciones para evitar ambigüedad '1/2 v' → '(1/2) v'
            coeff_display = f"({c_str})" if c.denominator != 1 else c_str
            # Si es negativo, el signo ya viene con el número
            if c < 0:
                term = f"{coeff_display} {v_name}"
            else:
                term = f"{coeff_display} {v_name}"

        if not parts:
            parts.append(term)
        else:
            if c > 0:
                parts.append(f"+ {term}")
            else:
                parts.append(term)

    if not parts:
        return "0 = 0"

    return " ".join(parts) + " = 0"
