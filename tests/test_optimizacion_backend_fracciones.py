"""Compatibilidad de conversiones exactas y copias defensivas matriciales."""
from fractions import Fraction

import pytest

from src.backend.excepciones import ErrorDatosMatriz
from src.backend.modelos.conversion_fracciones import convertir_fraccion, convertir_fila_fracciones
from src.backend.modelos.matriz import Matriz


@pytest.mark.parametrize("valor", [0, -3, True, False, 0.1, -0.0, Fraction(1, 1001), Fraction(-7, 3)])
def test_conversion_conserva_tipo_numerador_y_denominador(valor):
    """El resultado coincide exactamente con Fraction, incluidos flotantes binarios y booleanos."""
    esperado = Fraction(valor)
    actual = convertir_fraccion(valor)
    assert type(actual) is Fraction
    assert (actual.numerator, actual.denominator) == (esperado.numerator, esperado.denominator)


@pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan"), None, object()])
def test_conversion_conserva_excepcion_y_mensaje(valor):
    """Las entradas no convertibles conservan clase de excepción y mensaje de Fraction."""
    with pytest.raises((ValueError, OverflowError, TypeError)) as esperado:
        Fraction(valor)
    with pytest.raises(type(esperado.value)) as actual:
        convertir_fraccion(valor)
    assert str(actual.value) == str(esperado.value)


def test_solo_reutiliza_fraccion_canonica_y_filas_independientes():
    """Las subclases se convierten a Fraction base y la lista devuelta no comparte estructura."""
    class FraccionEspecial(Fraction):
        """Representa un racional con un tipo externo al contrato canónico."""

    canonica = Fraction(2, 3)
    especial = FraccionEspecial(3, 7)
    fila = [canonica, especial, 1, 0.1]
    actual = convertir_fila_fracciones(fila)
    assert actual == [Fraction(valor) for valor in fila]
    assert all(type(valor) is Fraction for valor in actual)
    assert actual[0] is canonica
    assert actual[1] is not especial
    actual[0] = Fraction(9)
    assert fila[0] is canonica
    assert convertir_fila_fracciones([]) == []


def test_clonar_conserva_revalidacion_tipo_base_y_despacho_del_constructor():
    """La copia reinterpreta celdas editadas y sigue devolviendo Matriz sin compartir filas."""
    class MatrizEspecial(Matriz):
        """Permite comprobar el tipo histórico de retorno de clonar."""

    matriz = MatrizEspecial(2, 2, [[1, 2], [3, 4]])
    matriz.datos[0][0] = "1/1001"
    clon = matriz.clonar()
    assert type(clon) is Matriz
    assert clon.datos == [[Fraction(1, 1001), 2], [3, 4]]
    assert type(clon.datos[0][0]) is Fraction
    assert clon.datos is not matriz.datos
    assert all(izquierda is not derecha for izquierda, derecha in zip(clon.datos, matriz.datos))
    clon.establecer(1, 1, 8)
    assert matriz.obtener(1, 1) == 4
    matriz.datos[1].pop()
    with pytest.raises(ErrorDatosMatriz, match="Fila 2 tiene 1 columnas; se esperaban 2."):
        matriz.clonar()


def test_clonar_conserva_prioridad_de_errores_y_normalizacion():
    """La forma completa se valida antes del contenido y no se elude la conversión pública."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    matriz.datos[0][0] = "abc"
    matriz.datos[1].pop()
    with pytest.raises(ErrorDatosMatriz, match="Fila 2 tiene 1 columnas; se esperaban 2."):
        matriz.clonar()
    matriz.datos[1].append(4)
    with pytest.raises(ErrorDatosMatriz, match="Valor no parseable como número: 'abc'."):
        matriz.clonar()


@pytest.mark.parametrize("filas", [0, 1])
def test_clonar_conserva_error_de_fila_malformada_antes_de_dimensiones(filas):
    """Incluso una fila no admitida mantiene el error histórico anterior a validar dimensiones."""
    matriz = Matriz(1, 1)
    matriz.datos = [7]
    matriz.filas = filas
    with pytest.raises(TypeError) as error:
        matriz.clonar()
    assert str(error.value) == "'int' object is not subscriptable"
