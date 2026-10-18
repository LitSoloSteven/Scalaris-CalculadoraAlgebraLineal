"""Preparación analítica y serialización de ecuaciones geométricas."""
from src.backend.geometria.clasificacion import clasificar_ecuacion
from src.backend.geometria.coordenadas import a_flotante_seguro
from src.backend.resolutores.operaciones_vectores.formateadores import formatear_expresion_lineal
from src.backend.utilidades.formateadores import numero_a_latex


def construir_ecuaciones(coeficientes: list, independientes: list, dimension: int) -> tuple[list | None, list]:
    """Devuelve ecuaciones serializables e interceptos; None si no admite flotantes."""
    ecuaciones, valores_rango = [], []
    variables = ["x", "y", "z"][:dimension]
    for indice, fila in enumerate(coeficientes):
        termino = independientes[indice]
        aproximados = [a_flotante_seguro(valor) for valor in fila]
        termino_aproximado = a_flotante_seguro(termino)
        if any(valor is None for valor in aproximados) or termino_aproximado is None:
            return None, []
        ecuaciones.append({
            "indice": indice, "tipo": clasificar_ecuacion(fila, termino, dimension),
            "coeficientes": aproximados, "coeficientes_exactos": [str(valor) for valor in fila],
            "objetivo": termino_aproximado, "objetivo_exacto": str(termino),
            "latex": f"{formatear_expresion_lineal(fila, variables)} = {numero_a_latex(termino)}",
        })
        valores_rango.extend(_interceptos(fila, termino))
    return ecuaciones, valores_rango


def _interceptos(coeficientes: list, termino) -> list:
    interceptos = []
    for coeficiente in coeficientes:
        if coeficiente != 0:
            valor = a_flotante_seguro(termino / coeficiente)
            if valor is not None:
                interceptos.append(valor)
    return interceptos
