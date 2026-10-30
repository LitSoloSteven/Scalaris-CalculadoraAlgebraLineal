"""Catálogo declarativo de pilares, herramientas y escenas de Scalaris."""
from src.frontend.navegacion.modelo import Pilar, Herramienta

INICIO_HABILITADO: bool = True
RUTA_INICIO: str = "/"
TITULO_PAGINA_INICIO: str = "Inicio | Scalaris"

ESCENAS_VISUALIZADOR: tuple[tuple[str, str, str, str, str], ...] = (
    ("rectas-planos", "Rectas y planos", "Rectas", "Sistemas de 2 y 3 variables", "escena_rectas_planos"),
    ("vectores", "Vectores", "Vectores", "Suma y escalamiento de u y v", "vectores"),
    ("combinacion", "Combinación lineal", "Combinación", "Cómo se forma b con tus vectores", "escena_combinacion"),
)

_ETIQUETAS_CORTAS: dict[str, str] = {
    "sistemas": "Sistemas",
    "vectores": "Vectores",
    "matrices": "Matrices",
    "inversa": "Inversa",
    "determinantes": "Determinantes",
    "factorizacion_lu": "LU",
    "bases": "Bases",
    "romanos": "Romanos",
    "leontief": "Leontief",
    "transformaciones": "Transformaciones",
}

PILARES: tuple[Pilar, ...] = (
    Pilar(
        identificador="algebra",
        nombre="Álgebra lineal",
        icono="algebra_lineal",
        nombre_corto="Álgebra lineal",
        prefijo="/algebra-lineal",
    ),
    Pilar(
        identificador="visualizador",
        nombre="Visualizador geométrico",
        icono="geometria",
        nombre_corto="Visualizador",
        prefijo="/visualizador",
    ),
    Pilar(
        identificador="utilidades",
        nombre="Utilidades numéricas",
        icono="utilidades",
        nombre_corto="Utilidades",
        prefijo="/utilidades",
    ),
)

_PILARES_POR_IDENTIFICADOR: dict[str, Pilar] = {pilar.identificador: pilar for pilar in PILARES}

HERRAMIENTAS: tuple[Herramienta, ...] = (
    Herramienta(
        identificador="sistemas",
        nombre="Sistemas de ecuaciones",
        descriptor="SEL: Gauss y Gauss-Jordan",
        ruta="/algebra-lineal/sistemas",
        identificador_pilar="algebra",
        icono="sistemas_lineales",
        titulo_pagina="Sistemas de ecuaciones lineales (SEL) | Scalaris",
        ejemplo_latex=r"A\mathbf{x} = \mathbf{b}",
        habilitada=True,
    ),
    Herramienta(
        identificador="vectores",
        nombre="Vectores",
        descriptor="Operaciones y combinación lineal",
        ruta="/algebra-lineal/vectores",
        identificador_pilar="algebra",
        icono="vectores",
        titulo_pagina="Vectores | Scalaris",
        ejemplo_latex=r"c_1\mathbf{v}_1 + c_2\mathbf{v}_2 = \mathbf{b}",
        habilitada=True,
    ),
    Herramienta(
        identificador="matrices",
        nombre="Matrices",
        descriptor="Expresiones, transpuesta y producto",
        ruta="/algebra-lineal/matrices",
        identificador_pilar="algebra",
        icono="operaciones_matrices",
        titulo_pagina="Matrices | Scalaris",
        ejemplo_latex=r"2A - B(C - D^{T})",
        habilitada=True,
    ),
    Herramienta(
        identificador="inversa",
        nombre="Matriz inversa",
        descriptor="Gauss-Jordan sobre [A | I]",
        ruta="/algebra-lineal/inversa",
        identificador_pilar="algebra",
        icono="matriz_inversa",
        titulo_pagina="Matriz inversa | Scalaris",
        ejemplo_latex=r"A^{-1}",
        habilitada=True,
    ),
    Herramienta(
        identificador="determinantes",
        nombre="Determinantes",
        descriptor="Triangulación LU con aritmética exacta",
        ruta="/algebra-lineal/determinantes",
        identificador_pilar="algebra",
        icono="determinantes",
        titulo_pagina="Determinantes | Scalaris",
        ejemplo_latex=r"\det(A)",
        habilitada=True,
    ),
    Herramienta(
        identificador="factorizacion_lu",
        nombre="Factorización LU",
        descriptor="PA = LU con pivoteo parcial",
        ruta="/algebra-lineal/factorizacion-lu",
        identificador_pilar="algebra",
        icono="factorizacion_lu",
        titulo_pagina="Factorización LU | Scalaris",
        ejemplo_latex=r"PA = LU",
        habilitada=True,
    ),
    Herramienta(
        identificador="visualizador",
        nombre="Rectas, planos y vectores",
        descriptor="Escenas interactivas en R² y R³",
        ruta="/visualizador",
        identificador_pilar="visualizador",
        icono="geometria",
        titulo_pagina="Visualizador geométrico | Scalaris",
        ejemplo_latex=r"\mathbf{x} = \mathbf{p} + t\,\mathbf{d}",
        habilitada=True,
    ),
    Herramienta(
        identificador="bases",
        nombre="Conversor de bases",
        descriptor="Decimal, binario, octal y hexadecimal",
        ruta="/utilidades/bases",
        identificador_pilar="utilidades",
        icono="conversor_bases",
        titulo_pagina="Conversor de bases | Scalaris",
        ejemplo_latex=r"1010_2 = 10_{10}",
        habilitada=True,
    ),
    Herramienta(
        identificador="romanos",
        nombre="Números romanos",
        descriptor="Suma, resta y multiplicación",
        ruta="/utilidades/romanos",
        identificador_pilar="utilidades",
        icono="romanos",
        titulo_pagina="Números romanos | Scalaris",
        ejemplo_latex=r"\text{XIV} + \text{IX} = \text{XXIII}",
        habilitada=True,
    ),
    Herramienta(
        identificador="leontief",
        nombre="Modelo de Leontief",
        descriptor="Insumo-producto: x = (I - C)^(-1) d",
        ruta="/algebra-lineal/leontief",
        identificador_pilar="algebra",
        icono="matriz_inversa",
        titulo_pagina="Modelo de Leontief | Scalaris",
        ejemplo_latex=r"x = (I - C)^{-1}\,d",
        habilitada=True,
    ),
    Herramienta(
        identificador="transformaciones",
        nombre="Transformaciones Lineales",
        descriptor="ker(T), Im(T), rango y nulidad",
        ruta="/algebra-lineal/transformaciones",
        identificador_pilar="algebra",
        icono="operaciones_matrices",
        titulo_pagina="Transformaciones Lineales | Scalaris",
        ejemplo_latex=r"T: \mathbb{R}^n \to \mathbb{R}^m",
        habilitada=True,
    ),
)

_HERRAMIENTAS_POR_IDENTIFICADOR: dict[str, Herramienta] = {herramienta.identificador: herramienta for herramienta in HERRAMIENTAS}

ORDEN_NAVEGACION_PLANA: tuple[str, ...] = (
    "sistemas",
    "matrices",
    "inversa",
    "determinantes",
    "factorizacion_lu",
    "vectores",
    "leontief",
    "transformaciones",
    "visualizador",
    "bases",
    "romanos",
)
