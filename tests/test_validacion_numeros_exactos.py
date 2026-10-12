"""Validación exacta de números y conservación de precisión en ecuaciones."""
from fractions import Fraction
from src.backend.utils.validators import MatrixValidator
from src.backend.utils.parsers import SystemParser


def test_numero_exacto_conserva_denominador_grande():
    """La fracción conserva su tipo y denominador sin aproximación."""
    valido, valor, mensaje = MatrixValidator.parse_number_exact("1/1001")
    assert valido, mensaje
    assert isinstance(valor, Fraction), f"Tipo incorrecto: {type(valor).__name__}"
    assert valor == Fraction(1, 1001)


def test_numero_aproximado_devuelve_flotante_para_interfaz():
    """La variante aproximada conserva el tipo que espera su consumidor."""
    valido, valor, mensaje = MatrixValidator.parse_number("1/1001")
    assert valido, mensaje
    assert isinstance(valor, float)


def test_flotante_se_normaliza_como_fraccion_simple():
    """Un decimal representable recupera la fracción exacta esperada."""
    valido, valor, mensaje = MatrixValidator.parse_number_exact(0.1)
    assert valido
    assert valor == Fraction(1, 10)


def test_variantes_numericas_comparten_mensaje_de_error():
    """La división por cero comunica el mismo error en ambas variantes."""
    valido, _, mensaje_exacto = MatrixValidator.parse_number_exact("1/0")
    assert not valido and "División por cero" in mensaje_exacto
    valido_aproximado, _, mensaje_aproximado = MatrixValidator.parse_number("1/0")
    assert not valido_aproximado
    assert mensaje_aproximado == mensaje_exacto, "Los mensajes deben ser idénticos"


def test_numero_rechaza_cadena_invalida():
    """Una cadena no numérica devuelve el error de validación."""
    valido, _, mensaje = MatrixValidator.parse_number_exact("abc")
    assert not valido and "no es un número" in mensaje


def test_analizador_sistemas_conserva_denominador_grande():
    """El coeficiente de la ecuación conserva la precisión racional."""
    valido, matriz, variables, mensaje = SystemParser.parse_system("1/1001 x + y = 1\nx + y = 2")
    assert valido, mensaje
    valor = matriz.get(0, 0)
    assert isinstance(valor, Fraction), f"Esperado Fraction, obtenido {type(valor).__name__}"
    assert valor == Fraction(1, 1001)


def test_analizador_sistemas_interpreta_coeficientes_enteros():
    """El entero se representa con el tipo racional del dominio."""
    valido, matriz, variables, mensaje = SystemParser.parse_system("2x + 3y = 8\nx - y = 1")
    assert valido, mensaje
    valor = matriz.get(0, 0)
    assert isinstance(valor, Fraction) and valor == 2


def test_analizador_sistemas_interpreta_fracciones_negativas():
    """El signo negativo forma parte del coeficiente racional."""
    valido, matriz, variables, mensaje = SystemParser.parse_system("-1/2 x + y = 0\nx + y = 1")
    assert valido, mensaje
    valor = matriz.get(0, 0)
    assert valor == Fraction(-1, 2), f"Esperado -1/2, obtenido {valor}"
