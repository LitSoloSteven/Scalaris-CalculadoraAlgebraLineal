"""Presentacion de pasos y comprobaciones numericas de una inversa."""
from src.backend.constantes import EXITO
from src.backend.modelos.matriz import Matriz
from src.backend.modelos.calculo_matricial import es_identidad
from src.backend.resolutores.operaciones_matrices.formateadores import matriz_a_latex, matriz_particionada_a_latex


def formatear_pasos_inversa(pasos: list[dict], dimension: int, construir_latex: bool) -> list[dict]:
    """Devuelve pasos particionados de dimension a partir de eventos; LaTeX es opcional."""
    formateados = []
    for indice, paso in enumerate(pasos):
        matriz = paso.get("matriz")
        latex = matriz_particionada_a_latex(matriz, dimension) if (matriz and construir_latex) else None
        descripcion = paso.get("descripcion", "")
        if indice == 0:
            descripcion = descripcion.replace("[A|b]", "[A|I]")
        formateados.append({"descripcion": descripcion, "matriz": matriz, "detalle_latex": latex})
    return formateados


def presentar_producto_inversa(producto: Matriz | None, dimension: int, inverso: bool) -> dict:
    """Devuelve la comprobacion y LaTeX del producto calculado, segun orden y dimension."""
    coincide = es_identidad(producto, dimension)
    propiedad = "A^{-1} \\cdot A = I" if inverso else "A \\cdot A^{-1} = I"
    palabra_estado = "Correcto" if coincide else "Incorrecto"
    izquierda = "A^{-1}" if inverso else "A"
    derecha = "A" if inverso else "A^{-1}"
    latex = matriz_a_latex(producto) if producto else ""
    return {
        "propiedad": propiedad, "nombre_izquierdo": izquierda, "nombre_derecho": derecha,
        "descripcion": f"Verificación {'A⁻¹·A' if inverso else 'A·A⁻¹'} = I.",
        "se_cumple": coincide, "coincide": coincide, "matriz_producto_latex": latex,
        "detalle_latex": f"{izquierda} \\cdot {derecha} = {latex} \\quad (\\text{{{palabra_estado}}})",
    }


def presentar_propiedad_transpuesta(producto: Matriz | None, inversa_transpuesta: Matriz) -> dict:
    """Devuelve comprobacion de transpuesta usando el producto y la inversa transpuesta calculados."""
    coincide = es_identidad(producto, inversa_transpuesta.filas)
    palabra = "Coinciden" if coincide else "Difieren"
    latex = matriz_a_latex(producto) if producto else ""
    return {
        "propiedad": "(A^T)^{-1} = (A^{-1})^T",
        "descripcion": "Verificación (Aᵀ)⁻¹ = (A⁻¹)ᵀ (PPT Inversa, pág. 11).",
        "se_cumple": coincide, "coincide": coincide,
        "inversa_transpuesta_latex": matriz_a_latex(inversa_transpuesta),
        "detalle_latex": f"(A^{{-1}})^T \\cdot A^T = {latex} \\quad (\\text{{{palabra}}})",
    }


def presentar_inversa(inversa: Matriz, meta: tuple, comprobaciones: tuple[dict, dict, dict]) -> dict:
    """Devuelve el contrato de exito desde inversa, determinante, aumentada, pasos y comprobaciones."""
    determinante, aumentada_latex, pasos = meta
    derecha, izquierda, transpuesta = comprobaciones
    dimension = inversa.filas
    return {
        "estado": EXITO, "mensaje": f"Inversa calculada con éxito ({dimension}×{dimension}).",
        "determinante": determinante, "matriz_aumentada_inicial_latex": aumentada_latex,
        "inversa": inversa, "inversa_latex": matriz_a_latex(inversa), "pasos": pasos,
        "paso_verificacion": derecha, "paso_verificacion_inverso": izquierda,
        "paso_propiedad_transpuesta": transpuesta,
    }
