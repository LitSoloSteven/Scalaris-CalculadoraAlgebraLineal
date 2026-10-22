"""Pasos pedagógicos de planteamiento previo y verificación formal para combinación lineal."""

from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import matriz_de_columnas
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import comprobar_producto
from src.backend.resolutores.operaciones_vectores.formateadores import (
    formatear_combinacion_lineal_vector,
    formatear_componente_escalar,
    formatear_expresion_lineal,
    formatear_variable_latex,
    formatear_vector_latex,
    matriz_aumentada_a_latex,
    vector_a_latex,
)
from src.backend.utilidades.formateadores import (
    formatear_fraccion_texto,
    numero_a_latex,
)


def _empaquetar_pasos_planteamiento(
    latex_pasos: tuple[str, str, str, str, str, str],
    matriz_aumentada: Matriz | None,
) -> list[dict]:
    """Empaqueta la lista de los 5 pasos con metadatos y matrices asociadas."""
    p1, p2, p3, p3_desc, p4, p5 = latex_pasos
    return [
        {"numero_paso": 1, "descripcion": "1. Ecuación vectorial con incógnitas (pesos):", "detalle_latex": p1, "matriz": matriz_aumentada},
        {"numero_paso": 2, "descripcion": "2. Multiplicación de los escalares dentro de cada vector:", "detalle_latex": p2, "matriz": matriz_aumentada},
        {"numero_paso": 3, "descripcion": p3_desc, "detalle_latex": p3, "matriz": matriz_aumentada},
        {"numero_paso": 4, "descripcion": "4. Sistema de ecuaciones lineales equivalente:", "detalle_latex": p4, "matriz": matriz_aumentada},
        {"numero_paso": 5, "descripcion": "5. Matriz aumentada del sistema [A | b]:", "detalle_latex": p5, "matriz": matriz_aumentada},
    ]


def _construir_paso_distribucion(vectores: list[Matriz], variable_latex: list[str], dimension: int) -> str:
    """Genera la expresión LaTeX para la distribución escalar en componentes."""
    vectores_latex = []
    for j, vector in enumerate(vectores):
        variable = variable_latex[j]
        filas = [formatear_componente_escalar(vector.obtener(i, 0), variable) for i in range(dimension)]
        vectores_latex.append(r"\begin{bmatrix} " + r" \\ ".join(filas) + r" \end{bmatrix}")
    return " + ".join(vectores_latex)


def construir_pasos_planteamiento(
    objetivo: Matriz,
    vectores: list[Matriz],
    nombres_variables: list[str],
    aumentada: Matriz | None = None,
) -> list[dict]:
    """Genera los 5 pasos de planteamiento pedagógico formal (David C. Lay)."""
    numero_vectores = len(vectores)
    dimension = objetivo.filas
    variable_latex = [formatear_variable_latex(nombre_variable) for nombre_variable in nombres_variables]
    b_latex = vector_a_latex(objetivo)

    paso1_terminos = [f"{variable} {vector_a_latex(vector)}" for variable, vector in zip(variable_latex, vectores)]
    paso1_latex = f"{' + '.join(paso1_terminos)} = {b_latex}"
    paso2_latex = f"{_construir_paso_distribucion(vectores, variable_latex, dimension)} = {b_latex}"

    filas_lado_izquierdo = [
        formatear_expresion_lineal([vectores[j].obtener(i, 0) for j in range(numero_vectores)], variable_latex)
        for i in range(dimension)
    ]
    paso3_latex = r"\begin{bmatrix} " + r" \\ ".join(filas_lado_izquierdo) + r" \end{bmatrix} = " + b_latex
    paso3_desc = (
        "3. Igualdad vectorial componente a componente (un solo vector):"
        if numero_vectores == 1
        else "3. Suma vectorial componente a componente (Lado Izquierdo):"
    )

    ecuaciones = [f"{filas_lado_izquierdo[i]} = {numero_a_latex(objetivo.obtener(i, 0))}" for i in range(dimension)]
    paso4_latex = r"\begin{cases} " + r" \\ ".join(ecuaciones) + r" \end{cases}"
    paso5_latex = matriz_aumentada_a_latex(vectores, objetivo)

    matriz_aumentada = aumentada.clonar() if aumentada else None
    return _empaquetar_pasos_planteamiento(
        (paso1_latex, paso2_latex, paso3_latex, paso3_desc, paso4_latex, paso5_latex),
        matriz_aumentada,
    )


def _evaluar_vector_y(y_matriz: Matriz) -> tuple[list[Fraction], str, str]:
    """Presenta las componentes exactas del producto ya calculado."""
    y_valores = [fila[0] for fila in y_matriz.datos]
    y_columna_latex = vector_a_latex(y_matriz)
    evaluado_latex = rf"\mathbf{{y}} = {y_columna_latex}"
    return y_valores, y_columna_latex, evaluado_latex


def _construir_detalle_latex_comprobacion(
    combinacion_simbolica: str,
    sustitucion_izquierda_latex: str,
    y_columna_latex: str,
    meta_comp: tuple[bool, list[Fraction], Matriz, list[str]],
) -> tuple[str, str]:
    """Devuelve la comparación LaTeX y el detalle con anotaciones de las matrices y variables."""
    coincide, y_valores, objetivo, nombres_variables = meta_comp
    b_columna_latex = vector_a_latex(objetivo)
    texto_estado = r"(\checkmark \text{ Coincide})" if coincide else r"(\times \text{ No coincide})"
    comparacion_latex = rf"\mathbf{{y}} = {y_columna_latex} \stackrel{{?}}{{=}} {b_columna_latex} = \mathbf{{b}} \quad {texto_estado}"
    simbolo_igualdad = "=" if coincide else r"\neq"
    componentes_resultado = " \\\\ ".join(numero_a_latex(valor_resultado) for valor_resultado in y_valores)
    componentes_objetivo = " \\\\ ".join(numero_a_latex(objetivo.obtener(i, 0)) for i in range(objetivo.filas))
    anotacion_matrices = rf"% {', '.join(nombres_variables)} \begin{{pmatrix}} {componentes_resultado} \end{{pmatrix}} \begin{{pmatrix}} {componentes_objetivo} \end{{pmatrix}}"
    comparacion_final = r"= \mathbf{b}" if coincide else rf"{simbolo_igualdad} {b_columna_latex} = \mathbf{{b}}"
    detalle_completo_latex = rf"\mathbf{{y}} = {combinacion_simbolica} = {sustitucion_izquierda_latex} = {y_columna_latex} {comparacion_final} \quad {texto_estado} {anotacion_matrices}"
    return comparacion_latex, detalle_completo_latex


def _construir_terminos_sustitucion(
    coeficientes: list[Fraction],
    vectores: list[Matriz],
) -> str:
    """Genera la sustitución de coeficientes y vectores en LaTeX."""
    terminos = []
    for coeficiente, vector in zip(coeficientes, vectores):
        c_f = Fraction(coeficiente)
        c_latex = numero_a_latex(c_f)
        term_c = rf"\left({c_latex}\right)" if c_f.denominator != 1 else f"({c_latex})"
        terminos.append(f"{term_c} {vector_a_latex(vector)}")
    return " + ".join(terminos)


def _construir_descripcion_comprobacion(
    coeficientes: list[Fraction],
    nombres_vector: list[str],
    valores_y: list[Fraction],
    objetivo: Matriz,
    coincide: bool,
) -> str:
    """Genera la descripción textual legible de la comprobación formal."""
    terminos_plano = [f"({formatear_fraccion_texto(coeficiente)})·{nombres_vector[j]}" for j, coeficiente in enumerate(coeficientes)]
    izquierda_plano = " + ".join(terminos_plano)
    y_plano = ", ".join(formatear_fraccion_texto(valor) for valor in valores_y)
    b_plano = ", ".join(formatear_fraccion_texto(objetivo.obtener(i, 0)) for i in range(objetivo.filas))
    return f"Comprobación formal: y = {izquierda_plano} = ({y_plano})ᵀ vs b = ({b_plano})ᵀ → {'CORRECTO' if coincide else 'FALLA'}"


def construir_paso_comprobacion(
    objetivo: Matriz,
    vectores: list[Matriz],
    coeficientes: list[Fraction],
    nombres_variables: list[str],
    nombres_vectores: list[str] | None = None,
) -> dict:
    """Construye el paso de verificación formal y = c_1·v_1 + ... + c_k·v_k."""
    numero_vectores, dimension = len(vectores), objetivo.filas
    nombres_vector = nombres_vectores if nombres_vectores else [f"v_{j + 1}" for j in range(numero_vectores)]
    variable_latex = [formatear_variable_latex(variable) for variable in nombres_variables]
    vector_latex = [formatear_vector_latex(nombre_vector) for nombre_vector in nombres_vector]

    formula_latex = rf"\mathbf{{y}} = {' + '.join([f'{variable}{vt}' for variable, vt in zip(variable_latex, vector_latex)])}"
    sub_izquierda_latex = _construir_terminos_sustitucion(coeficientes, vectores)
    sustitucion_latex = rf"\mathbf{{y}} = {sub_izquierda_latex}"

    desarrollo = comprobar_producto(matriz_de_columnas(vectores), Matriz(numero_vectores, 1, [[valor] for valor in coeficientes]), objetivo, "Ac=b")
    valores_y, y_columna_latex, vector_evaluado_latex = _evaluar_vector_y(desarrollo["producto"])
    coincide = desarrollo["coincide"]

    combinacion_simbolica = formatear_combinacion_lineal_vector(coeficientes, nombres_vector)
    comparacion_latex, detalle_completo_latex = _construir_detalle_latex_comprobacion(
        combinacion_simbolica, sub_izquierda_latex, y_columna_latex, (coincide, valores_y, objetivo, nombres_variables)
    )
    descripcion = _construir_descripcion_comprobacion(coeficientes, nombres_vector, valores_y, objetivo, coincide)

    return {
        "descripcion": descripcion,
        "formula_latex": formula_latex,
        "sustitucion_latex": sustitucion_latex,
        "vector_evaluado_latex": vector_evaluado_latex,
        "comparacion_latex": comparacion_latex,
        "detalle_latex": detalle_completo_latex,
        "coincide": coincide,
        "traza": desarrollo["traza"],
    }

