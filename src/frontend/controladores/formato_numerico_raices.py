"""Representación textual de magnitudes originales sin alterar su precisión."""


def numero(valor, completo: bool = False) -> str:
    """Formatea una magnitud con hasta 17 cifras y conserva los valores ausentes."""
    if valor is None:
        return "No disponible"
    return format(valor, ".17g" if completo else ".9g") if isinstance(valor, float) else str(valor)


def texto_intervalo(intervalo) -> str:
    """Representa los dos extremos con sus cifras internas, sin truncarlos."""
    return f"[{numero(intervalo[0], True)}, {numero(intervalo[1], True)}]"
