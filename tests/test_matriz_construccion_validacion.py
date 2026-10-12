"""Orden, mensajes y precisión del constructor matricial canónico."""
from fractions import Fraction
import pytest

from src.backend.excepciones import ErrorDatosMatriz
from src.backend.modelos.matriz import Matriz


@pytest.mark.parametrize("filas,columnas,mensaje", [
    (1.0, 2, "Las dimensiones deben ser enteros (filas=1.0, columnas=2)."),
    (1, "2", "Las dimensiones deben ser enteros (filas=1, columnas='2')."),
    (0, 2, "Las dimensiones deben ser positivas (recibido 0×2)."),
    (2, -1, "Las dimensiones deben ser positivas (recibido 2×-1)."),
])
def test_dimensiones_invalidas_conservan_mensaje(filas, columnas, mensaje):
    """Los tipos y límites de dimensiones mantienen la excepción y el texto exacto."""
    with pytest.raises(ErrorDatosMatriz) as error:
        Matriz(filas, columnas)
    assert str(error.value) == mensaje


@pytest.mark.parametrize("datos,mensaje", [
    ([], "Se esperaban 2 filas; datos trae 0."),
    ([[1, 2]], "Se esperaban 2 filas; datos trae 1."),
    ([[1], [2, 3]], "Fila 1 tiene 1 columnas; se esperaban 2."),
    ([["abc", 2], [3]], "Fila 2 tiene 1 columnas; se esperaban 2."),
])
def test_forma_se_valida_antes_de_normalizar_celdas(datos, mensaje):
    """Toda la estructura se comprueba antes de interpretar cualquier valor numérico."""
    with pytest.raises(ErrorDatosMatriz) as error:
        Matriz(2, 2, datos)
    assert str(error.value) == mensaje


def test_matriz_por_defecto_conserva_ceros_racionales_y_filas_independientes():
    """La construcción sin datos crea Fraction cero en filas sin almacenamiento compartido."""
    matriz = Matriz(2, 2)
    assert matriz.datos == [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]
    assert all(isinstance(valor, Fraction) for fila in matriz.datos for valor in fila)
    matriz.datos[0][0] = Fraction(1, 1001)
    assert matriz.datos[1][0] == Fraction(0)


def test_normalizacion_conserva_orden_y_precision_con_subclase():
    """La normalización mantiene el despacho de la subclase y el recorrido por filas."""
    class MatrizInstrumentada(Matriz):
        """Registra las celdas normalizadas delegando en la implementación original."""

        @staticmethod
        def _normalizar_valor(valor):
            valores.append(valor)
            return Matriz._normalizar_valor(valor)

    valores = []
    matriz = MatrizInstrumentada(2, 2, [["1/1001", "0.1"], [2, 0.5]])
    assert valores == ["1/1001", "0.1", 2, 0.5]
    assert matriz.datos == [[Fraction(1, 1001), Fraction(1, 10)], [2, Fraction(1, 2)]]


def test_dimensiones_booleanas_conservan_comportamiento_de_entero():
    """True mantiene su aceptación histórica como dimensión entera positiva."""
    matriz = Matriz(True, 1, [["2/3"]])
    assert matriz.filas is True
    assert matriz.datos == [[Fraction(2, 3)]]
