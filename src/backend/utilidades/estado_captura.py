"""Reglas de presencia y dimensiones de la captura matricial."""
from src.backend.modelos.construcciones import identidad
from src.backend.constantes import (
    DIMENSION_MAXIMA_SISTEMAS, DIMENSION_MAXIMA_LATEX_INVERSA, DIMENSION_CONFIRMACION_INVERSA,
)


def captura_vacia(valores, considerar_cero: bool = True) -> bool:
    """Devuelve si no hay texto significativo; opcionalmente trata cero como vacio."""
    vacios = ('', '0') if considerar_cero else ('',)
    return not any(valor and str(valor).strip() not in vacios for valor in valores)


def ajustar_numero_ecuaciones(actual: int, incremento: int) -> int:
    """Ajusta el numero editable entre una ecuacion y el limite del dominio."""
    return min(DIMENSION_MAXIMA_SISTEMAS, max(1, actual + incremento))


def opciones_transferencia_sistema(coeficientes: list) -> dict:
    """Determina las herramientas que admiten las dimensiones del sistema."""
    filas = len(coeficientes)
    numero_variables = len(coeficientes[0]) if filas else 0
    destinos = {'inversa': filas > 0 and filas == numero_variables, 'visualizador': False}
    if numero_variables in (2, 3):
        destinos['visualizador'] = True
    return destinos


def celdas_matriz(dimension: int = 3) -> tuple[tuple[str, ...], ...]:
    """Devuelve la identidad textual; lanza ValueError si la dimension es menor a uno."""
    if dimension < 1:
        raise ValueError(f'La dimension de la matriz debe ser mayor o igual a 1, recibido: {dimension}')
    return tuple(tuple(str(valor) for valor in fila) for fila in identidad(dimension).datos)


def opciones_dimension_inversa(dimension: int) -> dict:
    """Devuelve las capacidades y confirmacion correspondientes a una dimension."""
    return {'confirmar': dimension >= DIMENSION_CONFIRMACION_INVERSA,
            'mostrar_latex': dimension <= DIMENSION_MAXIMA_LATEX_INVERSA,
            'transferir_sistema': dimension <= DIMENSION_MAXIMA_SISTEMAS}
