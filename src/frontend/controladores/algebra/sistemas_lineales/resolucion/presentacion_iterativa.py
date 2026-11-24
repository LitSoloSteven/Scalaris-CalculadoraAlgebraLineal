"""Formato de presentación para valores racionales de métodos iterativos."""
from decimal import Decimal
from fractions import Fraction

DECIMALES_INICIALES = 2
MAXIMO_DECIMALES_VISIBLES = 16
FORMATO_EXACTO = 'exacto'
OPCIONES_DECIMALES = {
    **{cantidad: str(cantidad) for cantidad in range(MAXIMO_DECIMALES_VISIBLES + 1)},
    FORMATO_EXACTO: 'Valores exactos',
}
_UMBRAL_CIENTIFICO = 10 ** 12


def presentar_numero_iterativo(exacto: str, decimales: int | None) -> str:
    """Redondea solo el texto visible y conserva los valores exactos si decimales es None."""
    if decimales is None:
        return exacto
    numerador, _, denominador = exacto.partition('/')
    valor = Fraction(int(Decimal(numerador)), int(Decimal(denominador or '1')))
    if abs(valor) >= _UMBRAL_CIENTIFICO:
        return _notacion_cientifica(valor, decimales)
    texto = format(valor, f'.{decimales}f')
    if valor and Decimal(texto).is_zero():
        return _notacion_cientifica(valor, decimales)
    return texto


def _notacion_cientifica(valor: Fraction, decimales: int) -> str:
    magnitud = abs(valor)
    exponente = Decimal(magnitud.numerator).adjusted() - Decimal(magnitud.denominator).adjusted()
    escala = Fraction(10) ** exponente
    if magnitud < escala:
        exponente -= 1
        escala /= 10
    mantisa = format(valor / escala, f'.{decimales}f')
    if abs(Decimal(mantisa)) == 10:
        exponente += 1
        mantisa = format(Decimal(-1 if valor < 0 else 1), f'.{decimales}f')
    return f'{mantisa}e{exponente:+d}'


def presentar_vector_iterativo(valores: tuple[str, ...] | list[str], decimales: int | None) -> str:
    """Aplica la precisión de presentación a cada coordenada de un vector."""
    return '(' + ', '.join(presentar_numero_iterativo(valor, decimales) for valor in valores) + ')'
