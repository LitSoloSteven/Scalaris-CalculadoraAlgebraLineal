"""Exportación de coeficientes y términos independientes a ecuaciones algebraicas."""
from __future__ import annotations

from src.backend.utilidades.validadores import ValidadorMatriz


def _formatear_termino_variable(valor: str, j: int, tiene_terminos: bool) -> str | None:
    """Convierte un coeficiente escalar en un termino con variable xj."""
    if not valor or valor == "0":
        return None
    valida, _, _ = ValidadorMatriz.parsear_numero_exacto(valor)
    if not valida:
        return None
    signo = "-" if valor.startswith("-") else "+"
    valor_absoluto = valor.lstrip("+-").strip()
    coeficiente = "" if valor_absoluto == "1" or valor_absoluto == "" else valor_absoluto
    termino = f"{coeficiente}x{j+1}"
    if not tiene_terminos:
        return f"-{termino}" if signo == "-" else termino
    return f"{signo} {termino}"


def exportar_ecuaciones_desde_datos(
    coeficientes: list[list[str]], vector_b: list[str], conservar_forma: bool
) -> list[str]:
    """Convierte los coeficientes de matriz y terminos independientes a texto de ecuaciones."""
    ecuaciones: list[str] = []
    for i, fila in enumerate(coeficientes):
        terminos = []
        for j, valor in enumerate(fila):
            termino = _formatear_termino_variable(valor, j, len(terminos) > 0)
            if termino:
                terminos.append(termino)

        independiente = vector_b[i] if i < len(vector_b) else "0"
        if not terminos:
            cero_lado = "0x1" if conservar_forma else "0"
            ecuaciones.append(f"{cero_lado} = {independiente}" if (independiente and independiente != "0") else f"{cero_lado} = 0")
        else:
            ecuaciones.append(f"{' '.join(terminos)} = {independiente}")
    return ecuaciones
