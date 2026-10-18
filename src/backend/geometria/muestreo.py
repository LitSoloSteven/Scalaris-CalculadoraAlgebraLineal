"""Muestreo numérico de rectas y planos para su representación gráfica."""
from __future__ import annotations

TOLERANCIA_CERO_GRAFICO = 1e-12
MUESTRAS_PLANO = 12


def extremos_recta(coeficientes: list, termino: float, rango: list) -> tuple[list, list] | None:
    """Obtiene los extremos visibles con el mismo criterio de tolerancia gráfico."""
    horizontal, vertical = coeficientes
    if vertical is not None and abs(vertical) > TOLERANCIA_CERO_GRAFICO:
        inicio, fin = rango
        return [inicio, fin], [(termino - horizontal * inicio) / vertical, (termino - horizontal * fin) / vertical]
    if horizontal is not None and abs(horizontal) > TOLERANCIA_CERO_GRAFICO:
        coordenada = termino / horizontal
        return [coordenada, coordenada], rango
    return None


def espacio_lineal(inicio: float, fin: float, cantidad: int) -> list[float]:
    """Genera valores equiespaciados con los extremos incluidos."""
    if cantidad == 1:
        return [inicio]
    paso = (fin - inicio) / (cantidad - 1)
    return [inicio + i * paso for i in range(cantidad)]


def malla(eje_horizontal: list, eje_vertical: list) -> tuple[list, list]:
    """Devuelve coordenadas horizontales y verticales de una malla rectangular."""
    horizontal = [[valor for valor in eje_horizontal] for _ in eje_vertical]
    vertical = [[valor for _ in eje_horizontal] for valor in eje_vertical]
    return horizontal, vertical


def superficie_plano(coeficientes: list, termino: float, rango: list, cantidad: int = MUESTRAS_PLANO) -> tuple | None:
    """Muestrea un plano despejando el coeficiente de mayor valor absoluto."""
    magnitudes = [abs(valor) if valor is not None else 0 for valor in coeficientes]
    eje = magnitudes.index(max(magnitudes))
    if magnitudes[eje] <= TOLERANCIA_CERO_GRAFICO:
        return None
    valores = espacio_lineal(rango[0], rango[1], cantidad)
    horizontal, vertical = malla(valores, valores)
    return _resolver_malla(coeficientes, termino, eje, horizontal, vertical)


def _resolver_malla(coeficientes: list, termino: float, eje: int, horizontal: list, vertical: list) -> tuple:
    coeficiente_x, coeficiente_y, coeficiente_z = coeficientes
    if eje == 2:
        resuelta = [[(termino - coeficiente_x * coordenada_x - coeficiente_y * coordenada_y) / coeficiente_z
                     for coordenada_x, coordenada_y in zip(fila_x, fila_y)] for fila_x, fila_y in zip(horizontal, vertical)]
        return horizontal, vertical, resuelta
    if eje == 1:
        resuelta = [[(termino - coeficiente_x * coordenada_x - coeficiente_z * coordenada_z) / coeficiente_y
                     for coordenada_x, coordenada_z in zip(fila_x, fila_z)] for fila_x, fila_z in zip(horizontal, vertical)]
        return horizontal, resuelta, vertical
    resuelta = [[(termino - coeficiente_y * coordenada_y - coeficiente_z * coordenada_z) / coeficiente_x
                 for coordenada_y, coordenada_z in zip(fila_y, fila_z)] for fila_y, fila_z in zip(horizontal, vertical)]
    return resuelta, horizontal, vertical
