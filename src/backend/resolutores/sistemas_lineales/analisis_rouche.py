"""Analisis de sistemas lineales mediante el Teorema de Rouche-Frobenius."""

from src.backend.constantes import (
    SIN_SOLUCION,
    SOLUCION_UNICA,
)


def _generar_explicacion_rouche(
    estado: str,
    rango_a: int,
    rango_aumentada: int,
    numero_variables: int,
    es_homogeneo: bool,
) -> tuple[str, str]:
    """Genera la clasificacion y explicacion textual de Rouche-Frobenius."""
    if estado == SIN_SOLUCION:
        return (
            "Sistema Incompatible",
            f"rg(A) = {rango_a} < rg(A|b) = {rango_aumentada}. "
            "Por el Teorema de Rouché-Frobenius, el sistema no tiene solución (incompatible).",
        )
    if estado == SOLUCION_UNICA:
        if es_homogeneo:
            explicacion = (
                f"Sistema Homogéneo con rg(A) = {rango_a} = n ({numero_variables} incógnitas). "
                "Presenta únicamente la solución trivial única (x = 0)."
            )
        else:
            explicacion = (
                f"rg(A) = rg(A|b) = {rango_a} = n ({numero_variables} incógnitas). "
                "Por el Teorema de Rouché-Frobenius, el sistema presenta solución única (compatible determinado)."
            )
        return "Sistema Compatible Determinado", explicacion

    grados_libertad = numero_variables - rango_a
    if es_homogeneo:
        explicacion = (
            f"Sistema Homogéneo con rg(A) = {rango_a} < n ({numero_variables} incógnitas). "
            f"Presenta infinitas soluciones no triviales (dimensión del espacio nulo = {grados_libertad})."
        )
    else:
        explicacion = (
            f"rg(A) = rg(A|b) = {rango_a} < n ({numero_variables} incógnitas). "
            f"Por el Teorema de Rouché-Frobenius, presenta infinitas soluciones con {grados_libertad} variable(s) libre(s)."
        )
    return "Sistema Compatible Indeterminado", explicacion


def analizar_sistema_rouche(
    estado: str,
    rango_a: int,
    numero_variables: int,
    es_homogeneo: bool,
    pivotes: list[int],
) -> dict:
    """Construye el analisis de consistencia, Rouche y dependencia lineal."""
    rango_aumentada = rango_a + 1 if estado == SIN_SOLUCION else rango_a
    clasificacion, explicacion = _generar_explicacion_rouche(
        estado, rango_a, rango_aumentada, numero_variables, es_homogeneo
    )
    columnas_independientes = (rango_a == numero_variables)
    if columnas_independientes:
        conclusion_dependencia = (
            f"Las columnas de la matriz de coeficientes son LINEALMENTE INDEPENDIENTES (rango = {rango_a} = {numero_variables} variables)."
        )
    else:
        conclusion_dependencia = (
            f"Las columnas de la matriz de coeficientes son LINEALMENTE DEPENDIENTES (rango = {rango_a} < {numero_variables} variables)."
        )

    return {
        "es_homogeneo": es_homogeneo,
        "rango_a": rango_a,
        "rango_aumentada": rango_aumentada,
        "num_incognitas": numero_variables,
        "clasificacion_rouche": clasificacion,
        "explicacion_rouche": explicacion,
        "dependencia_lineal": {
            "son_linealmente_independientes": columnas_independientes,
            "conclusion": conclusion_dependencia,
        },
        "pivotes": pivotes,
    }
