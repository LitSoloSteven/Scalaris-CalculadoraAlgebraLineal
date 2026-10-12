"""Códigos, tokens, serialización y mensajes de los errores romanos."""
import json

import pytest

from src.backend.solvers.numeric_systems.roman_calculator import (
    RomanCalculator, RomanNumeralError, int_to_roman, roman_to_int,
    ERROR_OUT_OF_RANGE, ERROR_INVALID_SYNTAX, ERROR_NOT_CANONICAL,
    ERROR_ZERO_NOT_REPRESENTABLE, ERROR_NEGATIVE_NOT_REPRESENTABLE,
    ERROR_INVALID_TYPE, ERROR_EMPTY_INPUT, ERROR_OPERAND_NOT_SINGLE_DIGIT,
)


def test_error_conserva_codigo_y_token():
    """El constructor preserva código, entrada problemática y mensaje."""
    error = RomanNumeralError("mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM")
    assert error.code == ERROR_OUT_OF_RANGE
    assert error.invalid_token == "MMMM"
    assert str(error) == "mensaje"


def test_error_admite_ausencia_de_token():
    """Un error sin entrada problemática conserva un token nulo."""
    error = RomanNumeralError("mensaje", code=ERROR_ZERO_NOT_REPRESENTABLE)
    assert error.code == ERROR_ZERO_NOT_REPRESENTABLE
    assert error.invalid_token is None


def test_error_es_excepcion_de_valor():
    """El error romano conserva la clasificación de ValueError."""
    error = RomanNumeralError("x", code=ERROR_OUT_OF_RANGE)
    assert isinstance(error, ValueError)


def test_serializacion_con_token():
    """La serialización incluye exactamente las cuatro claves del contrato."""
    error = RomanNumeralError("mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM")
    assert error.to_dict() == {
        "status": "ERROR", "error_code": ERROR_OUT_OF_RANGE,
        "message": "mensaje", "token": "MMMM",
    }


def test_serializacion_sin_token():
    """La serialización conserva el token nulo y las demás propiedades."""
    error = RomanNumeralError("mensaje", code=ERROR_ZERO_NOT_REPRESENTABLE)
    datos = error.to_dict()
    assert datos["status"] == "ERROR"
    assert datos["error_code"] == ERROR_ZERO_NOT_REPRESENTABLE
    assert datos["message"] == "mensaje"
    assert datos["token"] is None


def test_serializacion_compatible_con_json():
    """Un ciclo JSON conserva el código y el token de la entrada."""
    error = RomanNumeralError("mensaje", code=ERROR_OUT_OF_RANGE, invalid_token="MMMM")
    datos = json.loads(json.dumps(error.to_dict()))
    assert datos["error_code"] == ERROR_OUT_OF_RANGE
    assert datos["token"] == "MMMM"


def test_conversion_entera_rechaza_tipo_invalido():
    """La conversión de un tipo no entero identifica el valor recibido."""
    with pytest.raises(RomanNumeralError) as captura:
        int_to_roman("X")
    assert captura.value.code == ERROR_INVALID_TYPE
    assert captura.value.invalid_token == "X"


def test_conversion_entera_rechaza_limite_superior():
    """El valor 4000 produce código de rango e identifica el operando."""
    with pytest.raises(RomanNumeralError) as captura:
        int_to_roman(4000)
    assert captura.value.code == ERROR_OUT_OF_RANGE
    assert captura.value.invalid_token == "4000"


def test_conversion_entera_rechaza_limite_inferior():
    """El cero produce el código de valor fuera de rango."""
    with pytest.raises(RomanNumeralError) as captura:
        int_to_roman(0)
    assert captura.value.code == ERROR_OUT_OF_RANGE


def test_conversion_romana_rechaza_tipo_invalido():
    """La entrada numérica produce el código de tipo inválido."""
    with pytest.raises(RomanNumeralError) as captura:
        roman_to_int(42)
    assert captura.value.code == ERROR_INVALID_TYPE
    assert captura.value.invalid_token == "42"


def test_conversion_romana_rechaza_entrada_vacia():
    """Los espacios solos producen el código de entrada vacía."""
    with pytest.raises(RomanNumeralError) as captura:
        roman_to_int("   ")
    assert captura.value.code == ERROR_EMPTY_INPUT


def test_conversion_romana_rechaza_caracteres_ajenos():
    """Los caracteres ajenos al alfabeto romano identifican la entrada."""
    with pytest.raises(RomanNumeralError) as captura:
        roman_to_int("ABC")
    assert captura.value.code == ERROR_INVALID_SYNTAX
    assert captura.value.invalid_token == "ABC"


def test_repeticion_de_cuatro_unos_es_sintaxis_invalida():
    """La expresión regular rechaza cuatro unos antes del control canónico."""
    with pytest.raises(RomanNumeralError) as captura:
        roman_to_int("IIII")
    assert captura.value.code == ERROR_INVALID_SYNTAX
    assert captura.value.invalid_token == "IIII"


def test_codigo_no_canonico_es_construible():
    """El código defensivo de forma no canónica mantiene su serialización."""
    error = RomanNumeralError(
        "'IIII' no es una forma canónica válida.",
        code=ERROR_NOT_CANONICAL, invalid_token="IIII",
    )
    assert error.code == ERROR_NOT_CANONICAL
    assert error.to_dict()["error_code"] == ERROR_NOT_CANONICAL
    assert error.to_dict()["token"] == "IIII"


def test_suma_fuera_de_rango_identifica_resultado():
    """La suma que alcanza 4000 identifica ese resultado como token."""
    with pytest.raises(RomanNumeralError) as captura:
        RomanCalculator.sumar("MMM", "M")
    assert captura.value.code == ERROR_OUT_OF_RANGE
    assert captura.value.invalid_token == "4000"


def test_resta_cero_carece_de_token():
    """El resultado cero usa su código específico y un token nulo."""
    with pytest.raises(RomanNumeralError) as captura:
        RomanCalculator.restar("V", "V")
    assert captura.value.code == ERROR_ZERO_NOT_REPRESENTABLE
    assert captura.value.invalid_token is None


def test_resta_negativa_carece_de_token():
    """Un resultado negativo usa su código específico y un token nulo."""
    with pytest.raises(RomanNumeralError) as captura:
        RomanCalculator.restar("III", "VII")
    assert captura.value.code == ERROR_NEGATIVE_NOT_REPRESENTABLE
    assert captura.value.invalid_token is None


def test_multiplicacion_rechaza_primer_operando_de_dos_digitos():
    """El primer operando inválido conserva su representación romana."""
    with pytest.raises(RomanNumeralError) as captura:
        RomanCalculator.multiplicar_un_digito("X", "II")
    assert captura.value.code == ERROR_OPERAND_NOT_SINGLE_DIGIT
    assert captura.value.invalid_token == "X"


def test_multiplicacion_rechaza_segundo_operando_de_dos_digitos():
    """El segundo operando inválido conserva su representación romana."""
    with pytest.raises(RomanNumeralError) as captura:
        RomanCalculator.multiplicar_un_digito("III", "XI")
    assert captura.value.code == ERROR_OPERAND_NOT_SINGLE_DIGIT
    assert captura.value.invalid_token == "XI"


def test_mensajes_de_error_preservados():
    """Los mensajes siguen permitiendo distinguir las cuatro causas."""
    with pytest.raises(RomanNumeralError, match="excede el límite"):
        RomanCalculator.sumar("MMM", "M")
    with pytest.raises(RomanNumeralError, match="cero"):
        RomanCalculator.restar("V", "V")
    with pytest.raises(RomanNumeralError, match="negativos"):
        RomanCalculator.restar("III", "VII")
    with pytest.raises(RomanNumeralError, match="no es de 1 dígito"):
        RomanCalculator.multiplicar_un_digito("X", "II")
