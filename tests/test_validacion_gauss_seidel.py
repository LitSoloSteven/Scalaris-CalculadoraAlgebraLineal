"""Validación de forma, celdas y límites de la entrada de Gauss-Seidel."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.gauss_seidel.contrato_gauss_seidel import (
    EntradaGaussSeidel, MatrizCrudaGaussSeidel,
)
from src.backend.resolutores.sistemas_lineales.gauss_seidel.validacion_gauss_seidel import (
    FalloValidacionGaussSeidel, preparar_captura, preparar_entrada,
)


def _entrada(
    matriz: MatrizCrudaGaussSeidel,
    vector_b: tuple | list,
    vector_inicial: tuple | list,
    tolerancia: Fraction | int | str = Fraction(1, 100),
    maximo: int = 5,
) -> EntradaGaussSeidel:
    return EntradaGaussSeidel(
        matriz_a=matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
    )


def _matriz(datos: list[list[int]]) -> MatrizCrudaGaussSeidel:
    return tuple(tuple(fila) for fila in datos)


def test_dimension_diez_se_acepta_y_once_se_rechaza() -> None:
    """El tope de sistemas admite diez variables y rechaza la once."""
    matriz = [[10 if fila == columna else 0 for columna in range(10)] for fila in range(10)]
    valido = preparar_entrada(_entrada(matriz, [10] * 10, [0] * 10))
    excesivo = preparar_entrada(_entrada([[0] * 11 for _ in range(11)], [0] * 11, [0] * 11))

    assert not isinstance(valido, FalloValidacionGaussSeidel)
    assert len(valido.matriz) == 10
    assert excesivo.codigo == "ENTRADA_INVALIDA"
    assert excesivo.diagnostico.campo == "matriz_a"


def test_matriz_rectangular_o_vacia_se_rechaza() -> None:
    """La forma se comprueba antes de convertir celdas."""
    rectangular = preparar_entrada(_entrada([[0, 0, 0], [0, 0, 0]], [0, 0], [0, 0]))
    sin_datos = preparar_entrada(_entrada([], [0], [0]))

    assert rectangular.codigo == "ENTRADA_INVALIDA"
    assert rectangular.diagnostico.campo == "matriz_a"
    assert sin_datos.codigo == "ENTRADA_INVALIDA"
    assert "vacía" in sin_datos.diagnostico.mensaje


def test_filas_irregulares_se_rechazan_antes_de_leer_celdas() -> None:
    """Una cuadrícula con filas desiguales no llega al cálculo."""
    resultado = preparar_entrada(_entrada([[1], [0, 1]], [1, 1], [0, 0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.fila == 1
    assert "fila 1" in resultado.diagnostico.mensaje.lower()


@pytest.mark.parametrize("campo,vector_b,vector_inicial", [
    ("vector_b", [1], [0, 0]),
    ("vector_inicial", [1, 1], [0]),
])
def test_vector_incompleto_identifica_el_campo(campo, vector_b, vector_inicial) -> None:
    """Cada vector debe tener una componente por ecuación."""
    resultado = preparar_entrada(
        _entrada(_matriz([[4, 1], [1, 3]]), vector_b, vector_inicial)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == campo


def test_captura_omite_el_inicio_y_usa_ceros() -> None:
    """La captura sin vector_inicial construye un cero por variable."""
    preparada = preparar_captura({
        "matriz_a": [[4, 1], [1, 3]],
        "vector_b": [2, 2],
        "tolerancia": "1/100",
        "maximo_iteraciones": 3,
    })

    assert not isinstance(preparada, FalloValidacionGaussSeidel)
    assert preparada.vector_inicial == (Fraction(0), Fraction(0))


@pytest.mark.parametrize("tolerancia", [0, Fraction(-1, 100), True, "0", "-1/3"])
def test_tolerancia_no_positiva_se_rechaza(tolerancia) -> None:
    """La tolerancia debe ser un racional estrictamente positivo."""
    resultado = preparar_entrada(
        _entrada(_matriz([[4, 1], [1, 3]]), [2, 2], [0, 0], tolerancia)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "tolerancia"


@pytest.mark.parametrize("maximo", [True, 0, 101, 1.5, "2"])
def test_maximo_fuera_de_rango_se_rechaza(maximo) -> None:
    """El máximo es un entero positivo dentro del tope documentado."""
    resultado = preparar_entrada(
        _entrada(_matriz([[4, 1], [1, 3]]), [2, 2], [0, 0], maximo=maximo)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "maximo_iteraciones"


def test_division_por_cero_y_booleano_se_ubican() -> None:
    """Los valores inválidos informan su coordenada sin llegar a dividir."""
    division = preparar_entrada(
        _entrada(_matriz([[4, 1], [1, 3]]), ["1/0", 2], [0, 0])
    )
    booleano = preparar_entrada(_entrada([[True]], [1], [0]))

    assert division.codigo == "ENTRADA_INVALIDA"
    assert division.diagnostico.fila == 1
    assert booleano.codigo == "ENTRADA_INVALIDA"
    assert (booleano.diagnostico.fila, booleano.diagnostico.columna) == (1, 1)


def test_diagonal_nula_ubica_la_ecuacion() -> None:
    """Una diagonal cero se informa con su fila y columna."""
    resultado = preparar_entrada(_entrada([[1, 2], [3, 0]], [1, 1], [0, 0]))

    assert resultado.codigo == "DIAGONAL_NULA"
    assert resultado.diagnostico.campo == "matriz_a"
    assert (resultado.diagnostico.fila, resultado.diagnostico.columna) == (2, 2)


def test_dominancia_estricta_se_informa_sin_bloquear() -> None:
    """Una matriz no dominante se valida y comunica su condición."""
    dominante = preparar_entrada(_entrada(_matriz([[4, 1], [1, 3]]), [2, 2], [0, 0]))
    no_dominante = preparar_entrada(_entrada(_matriz([[1, 2], [0, 1]]), [3, 1], [0, 0]))

    assert dominante.dominancia_estricta is True
    assert no_dominante.dominancia_estricta is False


def test_entrada_ajena_al_contrato_menciona_gauss_seidel() -> None:
    """El diagnóstico identifica el método cuando la entrada no cumple el contrato."""
    resultado = preparar_entrada(object())

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "entrada"
    assert "Gauss-Seidel" in resultado.diagnostico.mensaje


def test_captura_sin_campos_nombrados_se_rechaza() -> None:
    """La captura debe ser un mapeo con nombres."""
    resultado = preparar_captura(object())

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "entrada"


def test_las_entradas_no_se_modifican() -> None:
    """La validación usa una instantánea y conserva A, b y el vector inicial."""
    matriz = [[4, 1], [1, 3]]
    vector_b = [Fraction(2), Fraction(2)]
    vector_inicial = [Fraction(0), Fraction(0)]

    preparar_entrada(_entrada(matriz, vector_b, vector_inicial))

    assert matriz == [[4, 1], [1, 3]]
    assert vector_b == [Fraction(2), Fraction(2)]
    assert vector_inicial == [Fraction(0), Fraction(0)]


def test_fraccion_demasiado_grande_se_rechaza() -> None:
    """El tamaño de numerador y denominador se acota antes de iterar."""
    resultado = preparar_entrada(
        _entrada(_matriz([[4, 1], [1, 3]]), [Fraction(10 ** 5000), 2], [0, 0])
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.fila == 1
