"""Resultados, tipos y excepciones de operaciones de fila con términos nulos."""
from fractions import Fraction
import math

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.operaciones_filas import sumar_fila_multiplicada
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from src.backend.resolutores.sistemas_lineales.pasos_reduccion import RegistroPasosSistema


@pytest.mark.parametrize("destino", [Fraction(1, 1001), 2, True, -0.0, 1.5])
@pytest.mark.parametrize("origen", [Fraction(0), Fraction(2, 7), 0, False, -0.0])
@pytest.mark.parametrize("factor", [Fraction(-2, 3), Fraction(0), 2, 0.5, float("inf")])
def test_operaciones_conservan_valor_y_tipo_en_filas_mixtas(destino, origen, factor):
    """La identidad racional no cambia las promociones numéricas ni los flotantes no finitos."""
    esperado = destino + factor * origen
    fila = [destino]
    actual = sumar_fila_multiplicada(fila, [origen], factor)
    assert type(actual) is list and len(actual) == 1
    assert type(actual[0]) is type(esperado)
    if isinstance(esperado, float) and math.isnan(esperado):
        assert math.isnan(actual[0])
    else:
        assert actual[0] == esperado
        if isinstance(esperado, float):
            assert math.copysign(1, actual[0]) == math.copysign(1, esperado)
    assert fila == [destino]


@pytest.mark.parametrize("posicion", ["destino", "origen", "factor"])
def test_fracciones_personalizadas_conservan_operadores_y_errores(posicion):
    """Las subclases ejecutan sus operadores incluso cuando el término de origen es nulo."""
    class FraccionEspecial(Fraction):
        """Rechaza las operaciones para detectar atajos que ignoren operadores personalizados."""

        def __add__(self, otro):
            raise ArithmeticError("Suma personalizada")

        def __mul__(self, otro):
            raise ArithmeticError("Producto personalizado")

        def __rmul__(self, otro):
            raise ArithmeticError("Producto reflejado personalizado")

    datos = {"destino": Fraction(1, 3), "origen": Fraction(0), "factor": Fraction(2)}
    datos[posicion] = FraccionEspecial(datos[posicion])
    with pytest.raises(ArithmeticError):
        sumar_fila_multiplicada([datos["destino"]], [datos["origen"]], datos["factor"])


def test_filas_resultantes_son_nuevas_y_conservan_longitud_de_zip():
    """El resultado mantiene listas independientes y la truncación histórica de filas desiguales."""
    destino = [Fraction(1, 3), Fraction(2, 7)]
    origen = [Fraction(0)]
    resultado = sumar_fila_multiplicada(destino, origen, Fraction(2))
    assert resultado == [Fraction(1, 3)] and resultado is not destino
    assert resultado[0] is destino[0]
    resultado[0] = Fraction(9)
    assert destino == [Fraction(1, 3), Fraction(2, 7)]
    assert sumar_fila_multiplicada([], origen, None) == []


def test_instantaneas_siguen_siendo_matrices_y_listas_mutables_independientes():
    """Compartir racionales inmutables no comparte el almacenamiento mutable de pasos o entrada."""
    matriz = Matriz(3, 4, [[1, 1, 0, 2], [0, 1, 1, 2], [0, 0, 1, 1]])
    registro = RegistroPasosSistema(True)
    salida = ReductorFilas(matriz, 3, ConfiguracionReduccion(reduccion_completa=True), registro.registrar).reducir()
    assert salida["matriz_reducida"].datos == [[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1]]
    assert all(type(paso["matriz"]) is Matriz for paso in registro.pasos)
    assert all(type(fila) is list for paso in registro.pasos for fila in paso["matriz"].datos)
    registro.pasos[-1]["matriz"].datos[0][0] = 99
    assert registro.pasos[0]["matriz"].datos == matriz.datos
    assert salida["matriz_reducida"].obtener(0, 0) == 1
