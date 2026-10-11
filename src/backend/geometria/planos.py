"""Cálculo analítico de normales y coeficientes de planos en R³ con fracciones."""
from fractions import Fraction


def calcular_geometria_plano(
    direcciones: list[list[Fraction]],
    particular: list[Fraction],
) -> tuple[tuple[Fraction, Fraction, Fraction], Fraction]:
    """Calcula el vector normal n = d1 x d2 y el desplazamiento d = n · p."""
    dir_1 = direcciones[0]
    dir_2 = direcciones[1]

    norm_x = dir_1[1] * dir_2[2] - dir_1[2] * dir_2[1]
    norm_y = dir_1[2] * dir_2[0] - dir_1[0] * dir_2[2]
    norm_z = dir_1[0] * dir_2[1] - dir_1[1] * dir_2[0]

    desplazamiento = (
        norm_x * particular[0]
        + norm_y * particular[1]
        + norm_z * particular[2]
    )
    return (norm_x, norm_y, norm_z), desplazamiento
