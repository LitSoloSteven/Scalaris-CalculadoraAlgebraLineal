"""Compatibilidad de copias canónicas con normalización, extensiones y entradas malformadas."""
from fractions import Fraction

import pytest

from src.backend.modelos.copia_normalizada import copiar_datos_normalizados
from src.backend.modelos.matriz import Matriz


def test_copia_canonica_conserva_valores_tipos_y_filas_independientes():
    """Las listas se copian incluso si dos filas de entrada comparten su almacenamiento."""
    fraccion = Fraction(1, 1001)
    fila = [3, fraccion]
    datos = [fila, fila]
    copia = copiar_datos_normalizados(datos)
    assert copia == datos
    assert copia is not datos
    assert copia[0] is not copia[1] and copia[0] is not fila
    assert type(copia[0][0]) is int and copia[0][1] is fraccion
    copia[0][0] = 4
    assert fila[0] == copia[1][0] == 3
    assert copiar_datos_normalizados([]) == []


@pytest.mark.parametrize("datos", [None, [[True]], [[0.1]], [["1/3"]], [[object()]], ([],), [None]])
def test_entradas_no_canonicas_exigen_normalizacion_completa(datos):
    """Los valores y contenedores distintos de listas numéricas exactas reciben None."""
    assert copiar_datos_normalizados(datos) is None


def test_subclases_no_se_inspeccionan_antes_de_su_recorrido_historico():
    """La detección del atajo no ejecuta iteradores personalizados de contenedores ni escalares."""
    class ListaEspecial(list):
        """Rechaza recorridos adicionales durante la detección de datos canónicos."""

        def __iter__(self):
            raise AssertionError("Recorrido adicional")

    class FraccionEspecial(Fraction):
        """Mantiene el tipo personalizado para el normalizador matricial habitual."""

    assert copiar_datos_normalizados(ListaEspecial([[1]])) is None
    assert copiar_datos_normalizados([ListaEspecial([1])]) is None
    assert copiar_datos_normalizados([[FraccionEspecial(1, 3)]]) is None


def test_normalizador_personalizado_de_clase_recibe_cada_celda(monkeypatch):
    """Sustituir el normalizador desactiva el atajo incluso con datos numéricos canónicos."""
    llamadas = []

    def normalizar(valor):
        """Registra el orden y modifica el valor para hacer observable la delegación."""
        llamadas.append(valor)
        return valor + 10

    monkeypatch.setattr(Matriz, "_normalizar_valor", staticmethod(normalizar))
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    assert llamadas == [1, 2, 3, 4]
    assert matriz.datos == [[11, 12], [13, 14]]


def test_cambio_de_normalizador_durante_parseo_conserva_despacho(monkeypatch):
    """Las filas mixtas preservan la resolución del normalizador después de cada celda."""
    class TextoEspecial(str):
        """Cambia el normalizador al interpretar la primera celda textual."""

        def strip(self):
            """Sustituye el normalizador y devuelve el texto de la primera celda."""
            monkeypatch.setattr(Matriz, "_normalizar_valor", staticmethod(lambda valor: valor + 10))
            return "1"

    matriz = Matriz(1, 2, [[TextoEspecial("1"), 2]])
    assert matriz.datos == [[Fraction(1), 12]]


def test_subclase_de_matriz_conserva_normalizacion_y_tipo_de_clon():
    """El constructor de una subclase ejecuta su normalizador y clonar sigue devolviendo Matriz."""
    class MatrizEspecial(Matriz):
        """Permite observar el despacho virtual al recorrer los datos de entrada."""

        @staticmethod
        def _normalizar_valor(valor):
            return valor * 2

    matriz = MatrizEspecial(1, 2, [[2, 3]])
    assert matriz.datos == [[4, 6]]
    assert type(matriz.clonar()) is Matriz
    assert matriz.clonar().datos == [[4, 6]]
