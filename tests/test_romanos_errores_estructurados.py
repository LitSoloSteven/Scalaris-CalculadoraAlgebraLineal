"""Códigos, tokens, serialización y mensajes de los errores romanos."""
import json

import pytest

from src.backend.resolutores.sistemas_numericos.calculadora_romana import (
    CalculadoraRomana, ErrorNumeroRomano, entero_a_romano, romano_a_entero,
    ERROR_FUERA_DE_RANGO, ERROR_SINTAXIS_INVALIDA, ERROR_NO_CANONICO,
    ERROR_CERO_NO_REPRESENTABLE, ERROR_NEGATIVO_NO_REPRESENTABLE,
    ERROR_TIPO_INVALIDO, ERROR_ENTRADA_VACIA, ERROR_OPERANDO_NO_UN_DIGITO,
)


def test_error_conserva_codigo_y_token():
    """El constructor preserva código, entrada problemática y mensaje."""
    error = ErrorNumeroRomano("mensaje", codigo=ERROR_FUERA_DE_RANGO, token_invalido="MMMM")
    assert error.codigo == ERROR_FUERA_DE_RANGO
    assert error.token_invalido == "MMMM"
    assert str(error) == "mensaje"


def test_error_admite_ausencia_de_token():
    """Un error sin entrada problemática conserva un token nulo."""
    error = ErrorNumeroRomano("mensaje", codigo=ERROR_CERO_NO_REPRESENTABLE)
    assert error.codigo == ERROR_CERO_NO_REPRESENTABLE
    assert error.token_invalido is None


def test_error_es_excepcion_de_valor():
    """El error romano conserva la clasificación de ValueError."""
    error = ErrorNumeroRomano("x", codigo=ERROR_FUERA_DE_RANGO)
    assert isinstance(error, ValueError)


def test_serializacion_con_token():
    """La serialización incluye exactamente las claves del contrato unificado."""
    error = ErrorNumeroRomano("mensaje", codigo=ERROR_FUERA_DE_RANGO, token_invalido="MMMM")
    assert error.a_diccionario() == {
        "codigo_error": ERROR_FUERA_DE_RANGO, "estado": "ERROR",
        "mensaje": "mensaje", "token": "MMMM",
    }


def test_serializacion_sin_token():
    """La serialización conserva el token nulo y las demás propiedades."""
    error = ErrorNumeroRomano("mensaje", codigo=ERROR_CERO_NO_REPRESENTABLE)
    datos = error.a_diccionario()
    assert datos["estado"] == "ERROR"
    assert datos["codigo_error"] == ERROR_CERO_NO_REPRESENTABLE
    assert datos["mensaje"] == "mensaje"
    assert datos["token"] is None


def test_serializacion_compatible_con_json():
    """Un ciclo JSON conserva el código y el token de la entrada."""
    error = ErrorNumeroRomano("mensaje", codigo=ERROR_FUERA_DE_RANGO, token_invalido="MMMM")
    datos = json.loads(json.dumps(error.a_diccionario()))
    assert datos["codigo_error"] == ERROR_FUERA_DE_RANGO
    assert datos["token"] == "MMMM"


def test_conversion_entera_rechaza_tipo_invalido():
    """La conversión de un tipo no entero identifica el valor recibido."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        entero_a_romano("X")
    assert captura.value.codigo == ERROR_TIPO_INVALIDO
    assert captura.value.token_invalido == "X"


def test_conversion_entera_rechaza_limite_superior():
    """El valor 4000 produce código de rango e identifica el operando."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        entero_a_romano(4000)
    assert captura.value.codigo == ERROR_FUERA_DE_RANGO
    assert captura.value.token_invalido == "4000"


def test_conversion_entera_rechaza_limite_inferior():
    """El cero produce el código de valor fuera de rango."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        entero_a_romano(0)
    assert captura.value.codigo == ERROR_FUERA_DE_RANGO


def test_conversion_romana_rechaza_tipo_invalido():
    """La entrada numérica produce el código de tipo inválido."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        romano_a_entero(42)
    assert captura.value.codigo == ERROR_TIPO_INVALIDO
    assert captura.value.token_invalido == "42"


def test_conversion_romana_rechaza_entrada_vacia():
    """Los espacios solos producen el código de entrada vacía."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        romano_a_entero("   ")
    assert captura.value.codigo == ERROR_ENTRADA_VACIA


def test_conversion_romana_rechaza_caracteres_ajenos():
    """Los caracteres ajenos al alfabeto romano identifican la entrada."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        romano_a_entero("ABC")
    assert captura.value.codigo == ERROR_SINTAXIS_INVALIDA
    assert captura.value.token_invalido == "ABC"


def test_repeticion_de_cuatro_unos_es_sintaxis_invalida():
    """La expresión regular rechaza cuatro unos antes del control canónico."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        romano_a_entero("IIII")
    assert captura.value.codigo == ERROR_SINTAXIS_INVALIDA
    assert captura.value.token_invalido == "IIII"


def test_codigo_no_canonico_es_construible():
    """El código defensivo de forma no canónica mantiene su serialización."""
    error = ErrorNumeroRomano(
        "'IIII' no es una forma canónica válida.",
        codigo=ERROR_NO_CANONICO, token_invalido="IIII",
    )
    assert error.codigo == ERROR_NO_CANONICO
    assert error.a_diccionario()["codigo_error"] == ERROR_NO_CANONICO
    assert error.a_diccionario()["token"] == "IIII"


def test_suma_fuera_de_rango_identifica_resultado():
    """La suma que alcanza 4000 identifica ese resultado como token."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.sumar("MMM", "M")
    assert captura.value.codigo == ERROR_FUERA_DE_RANGO
    assert captura.value.token_invalido == "4000"


def test_resta_cero_carece_de_token():
    """El resultado cero usa su código específico y un token nulo."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.restar("V", "V")
    assert captura.value.codigo == ERROR_CERO_NO_REPRESENTABLE
    assert captura.value.token_invalido is None


def test_resta_negativa_carece_de_token():
    """Un resultado negativo usa su código específico y un token nulo."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.restar("III", "VII")
    assert captura.value.codigo == ERROR_NEGATIVO_NO_REPRESENTABLE
    assert captura.value.token_invalido is None


def test_multiplicacion_rechaza_primer_operando_de_dos_digitos():
    """El primer operando inválido conserva su representación romana."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.multiplicar_un_digito("X", "II")
    assert captura.value.codigo == ERROR_OPERANDO_NO_UN_DIGITO
    assert captura.value.token_invalido == "X"


def test_multiplicacion_rechaza_segundo_operando_de_dos_digitos():
    """El segundo operando inválido conserva su representación romana."""
    with pytest.raises(ErrorNumeroRomano) as captura:
        CalculadoraRomana.multiplicar_un_digito("III", "XI")
    assert captura.value.codigo == ERROR_OPERANDO_NO_UN_DIGITO
    assert captura.value.token_invalido == "XI"


def test_mensajes_de_error_preservados():
    """Los mensajes siguen permitiendo distinguir las cuatro causas."""
    with pytest.raises(ErrorNumeroRomano, match="excede el límite"):
        CalculadoraRomana.sumar("MMM", "M")
    with pytest.raises(ErrorNumeroRomano, match="cero"):
        CalculadoraRomana.restar("V", "V")
    with pytest.raises(ErrorNumeroRomano, match="negativos"):
        CalculadoraRomana.restar("III", "VII")
    with pytest.raises(ErrorNumeroRomano, match="no es de 1 dígito"):
        CalculadoraRomana.multiplicar_un_digito("X", "II")
