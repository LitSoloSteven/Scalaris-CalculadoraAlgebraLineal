"""Rechazo temprano de entradas numéricas costosas y precisión de entradas válidas."""
import time
from fractions import Fraction

import pytest

from src.backend.constants import MAX_NUMBER_STRING_LENGTH
from src.backend.exceptions import MatrixDataError
from src.backend.models.matrix import Matrix
from src.backend.utils.validators import MatrixValidator


MENSAJE_NOTACION = "Notación científica no soportada. Escribe el número con decimales o fracción."
MENSAJE_LONGITUD = f"El número excede la longitud máxima permitida ({MAX_NUMBER_STRING_LENGTH} caracteres)."


class TestRechazoParseoExacto:
    """Validación temprana de exponentes, longitud y prioridad de errores."""

    def test_exponente_enorme_rechazado_rapidamente(self):
        """El exponente enorme se rechaza antes de construir su valor entero."""
        inicio = time.perf_counter()
        valido, valor, mensaje = MatrixValidator.parse_number_exact("1e999999999")
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_NOTACION
        assert milisegundos < 50, f"Tardó {milisegundos:.2f} ms, se esperaba <50 ms"

    def test_exponente_positivo_rechazado(self):
        """La notación científica con exponente positivo no se admite."""
        valido, valor, mensaje = MatrixValidator.parse_number_exact("1E5")
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_NOTACION

    def test_exponente_negativo_rechazado(self):
        """La notación científica con exponente negativo no se admite."""
        valido, valor, mensaje = MatrixValidator.parse_number_exact("1e-4")
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_NOTACION

    def test_entrada_larga_rechazada_rapidamente(self):
        """La longitud excesiva se rechaza antes de construir una fracción."""
        inicio = time.perf_counter()
        valido, valor, mensaje = MatrixValidator.parse_number_exact("1" * 300)
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_LONGITUD
        assert milisegundos < 10, f"Tardó {milisegundos:.2f} ms, se esperaba <10 ms"

    def test_longitud_maxima_aceptada(self):
        """La entrada en el límite exacto de longitud sigue siendo válida."""
        entrada = "1" * MAX_NUMBER_STRING_LENGTH
        valido, valor, _ = MatrixValidator.parse_number_exact(entrada)
        assert valido is True

    def test_longitud_superior_al_limite_rechazada(self):
        """Un carácter adicional supera el límite permitido."""
        entrada = "1" * (MAX_NUMBER_STRING_LENGTH + 1)
        valido, valor, mensaje = MatrixValidator.parse_number_exact(entrada)
        assert valido is False
        assert mensaje == MENSAJE_LONGITUD

    def test_notacion_cientifica_tiene_prioridad_sobre_longitud(self):
        """Una entrada larga con exponente informa primero la notación."""
        entrada = "1" * 300 + "e1"
        valido, _, mensaje = MatrixValidator.parse_number_exact(entrada)
        assert valido is False
        assert mensaje == MENSAJE_NOTACION

    def test_espacios_no_ocultan_longitud_excesiva(self):
        """Se comprueba la longitud después de quitar espacios externos."""
        entrada = "  " + "1" * 300 + "  "
        valido, _, mensaje = MatrixValidator.parse_number_exact(entrada)
        assert valido is False
        assert mensaje == MENSAJE_LONGITUD


class TestEntradasValidasParseoExacto:
    """Precisión y mensajes del parseo exacto para entradas ordinarias."""

    @pytest.mark.parametrize("entrada, esperado", [
        ("1/3", Fraction(1, 3)), ("0.25", Fraction(1, 4)), ("-3", Fraction(-3, 1)),
        ("1001/1000", Fraction(1001, 1000)),
        ("-123456789012/987654321", Fraction(-123456789012, 987654321)),
        ("1/1001", Fraction(1, 1001)),
    ])
    def test_entradas_validas_aceptadas(self, entrada, esperado):
        """La entrada válida conserva su valor racional y carece de error."""
        valido, valor, mensaje = MatrixValidator.parse_number_exact(entrada)
        assert valido is True
        assert valor == esperado
        assert mensaje == ""

    def test_entrada_vacia_informa_campo_vacio(self):
        """Una entrada vacía conserva el mensaje de campo vacío."""
        valido, valor, mensaje = MatrixValidator.parse_number_exact("")
        assert valido is False
        assert mensaje == "El campo está vacío."

    def test_enteros_y_fracciones_aceptados(self):
        """Los valores enteros y las fracciones ya construidas son válidos."""
        assert MatrixValidator.parse_number_exact(5)[0] is True
        assert MatrixValidator.parse_number_exact(Fraction(1, 7))[0] is True


class TestConversionEstricta:
    """Rechazo temprano y exactitud de la conversión estricta a fracción."""

    def test_notacion_cientifica_rechazada_rapidamente(self):
        """El exponente enorme se rechaza en menos de cincuenta milisegundos."""
        inicio = time.perf_counter()
        valido, valor, mensaje = MatrixValidator._to_fraction_strict("1e999999999")
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_NOTACION
        assert milisegundos < 50

    def test_entrada_larga_rechazada_rapidamente(self):
        """La longitud excesiva se rechaza en menos de diez milisegundos."""
        inicio = time.perf_counter()
        valido, valor, mensaje = MatrixValidator._to_fraction_strict("1" * 300)
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert valido is False
        assert valor == Fraction(0)
        assert mensaje == MENSAJE_LONGITUD
        assert milisegundos < 10

    def test_notacion_cientifica_tiene_prioridad(self):
        """La notación científica se informa antes que el exceso de longitud."""
        valido, _, mensaje = MatrixValidator._to_fraction_strict("1" * 300 + "e1")
        assert valido is False
        assert mensaje == MENSAJE_NOTACION

    def test_entradas_validas_aceptadas(self):
        """La conversión conserva fracciones, decimales y enteros negativos."""
        for entrada, esperado in [
            ("1/3", Fraction(1, 3)), ("0.25", Fraction(1, 4)), ("-3", Fraction(-3, 1)),
        ]:
            valido, valor, mensaje = MatrixValidator._to_fraction_strict(entrada)
            assert valido is True
            assert valor == esperado
            assert mensaje == ""

    def test_entrada_vacia_informa_campo_vacio(self):
        """La conversión estricta conserva el mensaje de campo vacío."""
        valido, _, mensaje = MatrixValidator._to_fraction_strict("")
        assert valido is False
        assert mensaje == "El campo está vacío."


class TestRechazoNormalizacionMatricial:
    """La construcción y escritura de matrices rechazan entradas costosas."""

    def test_notacion_cientifica_lanza_error_rapidamente(self):
        """La construcción rechaza el exponente antes de materializarlo."""
        inicio = time.perf_counter()
        with pytest.raises(MatrixDataError) as captura:
            Matrix(1, 1, [["1e999999999"]])
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert MENSAJE_NOTACION in str(captura.value)
        assert milisegundos < 50

    def test_entrada_larga_lanza_error_rapidamente(self):
        """La construcción rechaza la longitud antes de convertir el número."""
        inicio = time.perf_counter()
        with pytest.raises(MatrixDataError) as captura:
            Matrix(1, 1, [["1" * 300]])
        milisegundos = (time.perf_counter() - inicio) * 1000
        assert MENSAJE_LONGITUD in str(captura.value)
        assert milisegundos < 10

    def test_notacion_cientifica_tiene_prioridad(self):
        """La normalización informa notación antes que longitud excesiva."""
        with pytest.raises(MatrixDataError) as captura:
            Matrix(1, 1, [["1" * 300 + "e1"]])
        assert MENSAJE_NOTACION in str(captura.value)

    def test_escritura_rechaza_notacion_cientifica(self):
        """La escritura de una celda aplica la misma protección numérica."""
        matriz = Matrix(1, 1, [[0]])
        with pytest.raises(MatrixDataError):
            matriz.set(0, 0, "1e999999999")

    def test_entrada_vacia_se_normaliza_a_cero(self):
        """La normalización matricial mantiene el cero para una celda vacía."""
        matriz = Matrix(1, 1, [[""]])
        assert matriz.get(0, 0) == Fraction(0)


class TestEntradasValidasNormalizacionMatricial:
    """La normalización conserva la precisión de las entradas válidas."""

    @pytest.mark.parametrize("entrada, esperado", [
        ("1/1001", Fraction(1, 1001)),
        ("-123456789012/987654321", Fraction(-123456789012, 987654321)),
        ("0.25", Fraction(1, 4)), ("-3", Fraction(-3, 1)),
    ])
    def test_entradas_validas_aceptadas(self, entrada, esperado):
        """La celda normalizada coincide exactamente con el racional esperado."""
        matriz = Matrix(1, 1, [[entrada]])
        assert matriz.get(0, 0) == esperado
