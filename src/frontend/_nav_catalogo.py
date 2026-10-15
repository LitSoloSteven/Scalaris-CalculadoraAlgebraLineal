"""Catálogo de datos de la taxonomía de navegación: pilares, herramientas y escenas."""
from __future__ import annotations

from src.frontend._nav_modelos import Pillar, Tool

VISUALIZER_SCENES: tuple[tuple[str, str, str, str, str], ...] = (
    ("rectas-planos", "Rectas y planos", "Rectas", "Sistemas de 2 y 3 variables", "escena_rectas_planos"),
    ("vectores", "Vectores", "Vectores", "Suma y escalamiento de u y v", "vectores"),
    ("combinacion", "Combinación lineal", "Combinación", "Cómo se forma b con tus vectores", "escena_combinacion"),
)

SHORT_LABELS: dict[str, str] = {
    "sistemas": "Sistemas",
    "vectores": "Vectores",
    "matrices": "Matrices",
    "inversa": "Inversa",
    "determinantes": "Determinantes",
    "bases": "Bases",
    "romanos": "Romanos",
}

PILLARS: tuple[Pillar, ...] = (
    Pillar(id="algebra", name="Álgebra lineal", icon="algebra_lineal", short_name="Álgebra lineal", prefix="/algebra-lineal"),
    Pillar(id="visualizador", name="Visualizador geométrico", icon="geometria", short_name="Visualizador", prefix="/visualizador"),
    Pillar(id="utilidades", name="Utilidades numéricas", icon="utilidades", short_name="Utilidades", prefix="/utilidades"),
)

TOOLS: tuple[Tool, ...] = (
    Tool(
        id="sistemas",
        name="Sistemas de ecuaciones",
        descriptor="SEL: Gauss y Gauss-Jordan",
        route="/algebra-lineal/sistemas",
        pillar_id="algebra",
        icon="sistemas_lineales",
        page_title="Sistemas de ecuaciones lineales (SEL) | Scalaris",
        example_latex=r"A\mathbf{x} = \mathbf{b}",
        enabled=True,
    ),
    Tool(
        id="vectores",
        name="Vectores",
        descriptor="Operaciones y combinación lineal",
        route="/algebra-lineal/vectores",
        pillar_id="algebra",
        icon="vectores",
        page_title="Vectores | Scalaris",
        example_latex=r"c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{b}",
        enabled=True,
    ),
    Tool(
        id="matrices",
        name="Matrices",
        descriptor="Expresiones, transpuesta y producto",
        route="/algebra-lineal/matrices",
        pillar_id="algebra",
        icon="operaciones_matrices",
        page_title="Matrices | Scalaris",
        example_latex=r"2A - B(C - D^{T})",
        enabled=True,
    ),
    Tool(
        id="inversa",
        name="Matriz inversa",
        descriptor="Gauss-Jordan sobre [A | I]",
        route="/algebra-lineal/inversa",
        pillar_id="algebra",
        icon="matriz_inversa",
        page_title="Matriz inversa | Scalaris",
        example_latex=r"A^{-1}",
        enabled=True,
    ),
    Tool(
        id="determinantes",
        name="Determinantes",
        descriptor="Cofactores y eliminación con pivoteo",
        route="/algebra-lineal/determinantes",
        pillar_id="algebra",
        icon="determinantes",
        page_title="Determinantes | Scalaris",
        example_latex=r"\det(A)",
        enabled=True,
    ),
    Tool(
        id="visualizador",
        name="Rectas, planos y vectores",
        descriptor="Escenas interactivas en R² y R³",
        route="/visualizador",
        pillar_id="visualizador",
        icon="geometria",
        page_title="Visualizador geométrico | Scalaris",
        example_latex=r"\mathbf{x} = \mathbf{p} + t\,\mathbf{d}",
        enabled=True,
    ),
    Tool(
        id="bases",
        name="Conversor de bases",
        descriptor="Decimal, binario, octal y hexadecimal",
        route="/utilidades/bases",
        pillar_id="utilidades",
        icon="conversor_bases",
        page_title="Conversor de bases | Scalaris",
        example_latex=r"1010_2 = 10_{10}",
        enabled=True,
    ),
    Tool(
        id="romanos",
        name="Números romanos",
        descriptor="Suma, resta y multiplicación",
        route="/utilidades/romanos",
        pillar_id="utilidades",
        icon="romanos",
        page_title="Números romanos | Scalaris",
        example_latex=r"\text{XIV} + \text{IX} = \text{XXIII}",
        enabled=True,
    ),
)

NAV_FLAT_ORDER: tuple[str, ...] = (
    "sistemas",
    "matrices",
    "inversa",
    "determinantes",
    "vectores",
    "visualizador",
    "bases",
    "romanos",
)

ORDEN_ITEMS_POR_PILAR: dict[str, tuple[str, ...]] = {
    "algebra": ("sistemas", "vectores", "matrices", "inversa", "determinantes"),
    "utilidades": ("bases", "romanos"),
}

ALIAS_PILARES: dict[str, str] = {
    "algebra-lineal": "algebra",
    "geometria": "visualizador",
    "utilidades-numericas": "utilidades",
}