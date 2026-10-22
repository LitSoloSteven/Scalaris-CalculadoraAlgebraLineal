"""Cálculo analítico de normales y coeficientes de planos en R³ con fracciones."""
from fractions import Fraction


def calcular_geometria_plano(
    direcciones: list[list[Fraction]],
    particular: list[Fraction],
) -> tuple[tuple[Fraction, Fraction, Fraction], Fraction]:
    """Calcula el vector normal n = d1 x d2 y el desplazamiento d = n · p."""
    dir_1 = direcciones[0]
    dir_2 = direcciones[1]

    normal_x = dir_1[1] * dir_2[2] - dir_1[2] * dir_2[1]
    normal_y = dir_1[2] * dir_2[0] - dir_1[0] * dir_2[2]
    normal_z = dir_1[0] * dir_2[1] - dir_1[1] * dir_2[0]

    desplazamiento = (
        normal_x * particular[0]
        + normal_y * particular[1]
        + normal_z * particular[2]
    )
    return (normal_x, normal_y, normal_z), desplazamiento
