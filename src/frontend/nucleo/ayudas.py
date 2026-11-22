"""Formato visual de pasos textuales y algebraicos para MathJax."""


def formatear_paso_mathjax(paso: str) -> str:
    """Envuelve el prefijo descriptivo de un paso en \\text{} para MathJax.
    Conserva las fórmulas posteriores a dos puntos y los pasos ya envueltos."""
    cadena = str(paso).strip()
    if cadena.startswith(r"\text"):
        return cadena
    encabezado, separador, resto = cadena.partition(":")
    if separador and encabezado and not any(caracter in encabezado for caracter in r"\{}^_="):
        return rf"\text{{{encabezado}:}}\;{resto}"
    return cadena
