"""Límites de copia y diagnóstico de entradas sobredimensionadas de Jacobi."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.contrato_jacobi import EntradaJacobi
from src.backend.resolutores.sistemas_lineales.jacobi import resolver_jacobi


def _entrada(matriz: Matriz, vector_b, vector_inicial) -> EntradaJacobi:
    return EntradaJacobi(
        matriz_a=matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=Fraction(1, 100),
        maximo_iteraciones=5,
    )


def _matriz(datos: list[list[int]]) -> Matriz:
    return Matriz(len(datos), len(datos[0]), datos)


def test_vector_sobredimensionado_no_se_copia_entero() -> None:
    """La copia del vector se detiene al superar la dimensión esperada."""
    class _VectorLargo(list):
        """Lista que falla si se consume más allá del límite permitido."""

        def __iter__(self):
            for indice, valor in enumerate(list.__iter__(self)):
                if indice > 2:
                    raise AssertionError("Se copió el vector completo.")
                yield valor

    vector_b = _VectorLargo([1] * 100_000)
    resultado = resolver_jacobi(_entrada(_matriz([[1]]), vector_b, [0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"


def test_fila_sobredimensionada_no_se_copia_entera() -> None:
    """La copia de una fila se detiene al superar el número de columnas."""
    class _FilaLarga(list):
        """Fila que falla si se consume más allá del límite permitido."""

        def __iter__(self):
            for indice, valor in enumerate(list.__iter__(self)):
                if indice > 2:
                    raise AssertionError("Se copió la fila completa.")
                yield valor

    matriz = _matriz([[1]])
    matriz.datos = [_FilaLarga([1] * 100_000)]
    resultado = resolver_jacobi(_entrada(matriz, [1], [0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "matriz_a"


def test_dimension_gigante_no_rompe_el_diagnostico() -> None:
    """El rango se informa sin interpolar un entero enorme."""
    matriz = _matriz([[1]])
    matriz.filas = 10 ** 5000
    resultado = resolver_jacobi(_entrada(matriz, [1], [0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "matriz_a"
