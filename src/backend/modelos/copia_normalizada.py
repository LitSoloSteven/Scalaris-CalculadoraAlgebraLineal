"""Copias de filas que el normalizador matricial canónico conserva sin transformación."""
from fractions import Fraction


def copiar_datos_normalizados(datos: object) -> list[list[int | Fraction]] | None:
    """Copia listas de int/Fraction exactos o devuelve None para usar la normalización completa."""
    if type(datos) is not list:
        return None
    if not all(type(fila) is list for fila in datos):
        return None
    if not all(type(valor) is Fraction or type(valor) is int for fila in datos for valor in fila):
        return None
    return [fila[:] for fila in datos]
