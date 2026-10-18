"""Normalización única del modelo matricial y ausencia de su alias retirado."""
from fractions import Fraction
import math
import pytest

from src.backend import modelos
from src.backend.modelos.matriz import Matriz
from src.backend.excepciones import ErrorDatosMatriz


def test_modelos_utilizan_la_misma_funcion_sin_alias():
    """El modelo publicado utiliza el normalizador canónico sin nombre duplicado."""
    assert modelos.Matriz._normalizar_valor is Matriz._normalizar_valor
    assert not hasattr(Matriz, "_normalize_val")


@pytest.mark.parametrize("valor,esperado", [
    (Fraction(1, 1001), Fraction(1, 1001)), (2, 2), (True, True),
    ("1/1001", Fraction(1, 1001)), ("0.1", Fraction(1, 10)),
    (" 2/3 ", Fraction(2, 3)), ("", Fraction(0)), (0.5, Fraction(1, 2)),
])
def test_normalizador_compartido_conserva_valor_y_tipo(valor, esperado):
    """La función común mantiene la precisión y los tipos históricos de cada celda."""
    actual = Matriz._normalizar_valor(valor)
    assert actual == esperado
    assert type(actual) is type(esperado)


@pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan")])
def test_flotantes_no_finitos_conservan_retorno_original(valor):
    """La deduplicación no introduce una validación matemática nueva para flotantes."""
    actual = Matriz._normalizar_valor(valor)
    assert actual is valor
    assert not math.isfinite(actual)


@pytest.mark.parametrize("valor,mensaje", [
    ("abc", "Valor no parseable como número: 'abc'."),
    ("1/0", "Valor no parseable como número: '1/0'."),
    ("1e999", "Notación científica no soportada. Escribe el número con decimales o fracción."),
    ("1" * 257, "El número excede la longitud máxima permitida (256 caracteres)."),
    (None, "Tipo no soportado en celda: NoneType."),
])
def test_rechazos_del_normalizador_conservan_tipo_y_texto(valor, mensaje):
    """Las guardas y errores conservan la excepción de dominio y su mensaje exacto."""
    with pytest.raises(ErrorDatosMatriz) as error:
        Matriz._normalizar_valor(valor)
    assert str(error.value) == mensaje
