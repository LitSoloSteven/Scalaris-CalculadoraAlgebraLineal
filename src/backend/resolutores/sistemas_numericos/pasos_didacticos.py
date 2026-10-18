"""Cálculos de trazabilidad numérica consumidos por los reproductores didácticos."""


def calcular_subtotal_expansion(terminos: list[dict], hasta_indice: int) -> int:
    """Suma los productos del prefijo de términos sin modificar sus datos."""
    return sum(termino["producto"] for termino in terminos[:hasta_indice + 1])


def desglosar_sumas_sucesivas(valor: int, cantidad: int) -> list[dict[str, int]]:
    """Devuelve índices y acumulados exactos de una multiplicación por sumas."""
    acumulado, pasos = 0, []
    for indice in range(1, cantidad + 1):
        acumulado += valor
        pasos.append({"indice": indice, "acumulado": acumulado})
    return pasos


def desglosar_bits(cadena_binaria: str) -> list[dict[str, int | str]]:
    """Devuelve cada bit y su peso posicional exacto para una representación breve."""
    return [
        {"bit": bit, "exponente": len(cadena_binaria) - 1 - indice,
         "peso": 2 ** (len(cadena_binaria) - 1 - indice)}
        for indice, bit in enumerate(cadena_binaria)
    ]
