"""Algoritmos geométricos de recorte a caja visual y cálculo de escala automática."""
import math
from src.backend.constantes import TOLERANCIA_CERO_GRAFICO


def recortar_recta_a_caja(
    punto: list[float],
    direccion: list[float],
    semi_ancho: float,
) -> tuple[float, float] | None:
    """Calcula el intervalo del parámetro t donde la recta intersecta la caja."""
    limite_inferior = -float("inf")
    limite_superior = float("inf")

    for componente_p, componente_d in zip(punto, direccion):
        if abs(componente_d) < TOLERANCIA_CERO_GRAFICO:
            if componente_p < -semi_ancho or componente_p > semi_ancho:
                return None
            continue
        parametro_min = (-semi_ancho - componente_p) / componente_d
        parametro_max = (semi_ancho - componente_p) / componente_d
        if parametro_min > parametro_max:
            parametro_min, parametro_max = parametro_max, parametro_min
        limite_inferior = max(limite_inferior, parametro_min)
        limite_superior = min(limite_superior, parametro_max)

    if (
        limite_inferior > limite_superior
        or limite_inferior == -float("inf")
        or limite_superior == float("inf")
    ):
        return None
    return limite_inferior, limite_superior


def _redondear_escala_125(semi_ancho: float) -> float:
    """Ajusta un semi-ancho hacia arriba según la serie geométrica 1, 2, 5."""
    exponente = math.floor(math.log10(semi_ancho))
    potencia_base = 10**exponente
    normalizado = semi_ancho / potencia_base

    if normalizado <= 1.0:
        factor_escala = 1.0
    elif normalizado <= 2.0:
        factor_escala = 2.0
    elif normalizado <= 5.0:
        factor_escala = 5.0
    else:
        factor_escala = 10.0

    return factor_escala * potencia_base


def calcular_rango_automatico(
    valores: list[float],
    *,
    minimo: float = 5.0,
    margen: float = 0.35,
) -> list[float]:
    """Calcula un rango simétrico [-ancho, ancho] con escala legible 1-2-5."""
    finitos = [valor for valor in valores if valor is not None and math.isfinite(valor)]
    if not finitos:
        return [-minimo, minimo]

    maximo_absoluto = max(abs(valor) for valor in finitos)
    semi_ancho = max(maximo_absoluto * (1.0 + margen), minimo)
    semi_ancho = min(semi_ancho, 1e6)

    if semi_ancho <= 0:
        return [-minimo, minimo]

    ancho_final = _redondear_escala_125(semi_ancho)
    return [-ancho_final, ancho_final]
