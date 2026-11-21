"""Etiquetas y valores iniciales de los controles de parada de bisección."""

DECIMALES_PRESENTACION_DEFECTO = 4
CRITERIOS = {
    "decimales": ("Precisión decimal", "Decimales de precisión d", 4),
    "relativo": ("Error relativo aproximado", "Porcentaje máximo (%)", "1"),
    "ancho": ("Ancho absoluto", "Tolerancia absoluta E (unidades de x)", "0.01"),
    "residuo": ("Residuo", "Tolerancia de residuo δ (unidades de f(x))", "0.1"),
    "iteraciones": ("Número fijo de iteraciones", "Número de iteraciones n", 10),
}


def condicion_criterio(tipo: str, parametro: int | float) -> str:
    """Describe la condición solicitada sin decidir si una fila la satisface."""
    valor = str(parametro)
    condiciones = {"decimales": f"b − a < 10^(−{valor}) · unidades de x",
                   "relativo": f"|(cᵢ − cᵢ₋₁) / cᵢ| × 100 < {valor} %",
                   "ancho": f"b − a < {valor} · unidades de x",
                   "residuo": f"|f(c)| < {valor} · unidades de f(x)",
                   "iteraciones": f"Realizar {valor} iteraciones, salvo una salida excepcional"}
    return condiciones[tipo]
