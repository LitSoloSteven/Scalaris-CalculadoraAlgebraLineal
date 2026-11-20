"""Validación de forma, celdas y límites de la entrada del método de Jacobi."""
from fractions import Fraction

import pytest

from src.backend.resolutores.sistemas_lineales.contrato_jacobi import EntradaJacobi, MatrizCrudaJacobi
from src.backend.resolutores.sistemas_lineales.jacobi import resolver_jacobi


def _entrada(
    matriz: MatrizCrudaJacobi,
    vector_b: tuple | list,
    vector_inicial: tuple | list,
    tolerancia: Fraction | int | str = Fraction(1, 100),
    maximo: int = 5,
) -> EntradaJacobi:
    return EntradaJacobi(
        matriz_a=matriz,
        vector_b=vector_b,
        vector_inicial=vector_inicial,
        tolerancia=tolerancia,
        maximo_iteraciones=maximo,
    )


def _matriz_cuadrada(datos: list[list[int]]) -> MatrizCrudaJacobi:
    return tuple(tuple(fila) for fila in datos)


def test_dimension_diez_resuelve_y_once_se_rechaza() -> None:
    """El tope de sistemas admite diez variables y rechaza la once."""
    matriz = [[10 if fila == columna else 0 for columna in range(10)] for fila in range(10)]
    valido = resolver_jacobi(_entrada(matriz, [10] * 10, [0] * 10))
    excesivo = resolver_jacobi(_entrada([[0] * 11 for _ in range(11)], [0] * 11, [0] * 11))

    assert valido.codigo == "SOLUCION_EXACTA"
    assert valido.aproximacion == (Fraction(1),) * 10
    assert excesivo.codigo == "ENTRADA_INVALIDA"
    assert excesivo.diagnostico.campo == "matriz_a"


def test_matriz_rectangular_o_vacia_se_rechaza() -> None:
    """La forma se comprueba antes de convertir celdas."""
    rectangular = resolver_jacobi(_entrada([[0, 0, 0], [0, 0, 0]], [0, 0], [0, 0]))
    sin_datos = resolver_jacobi(_entrada([], [0], [0]))

    assert rectangular.codigo == "ENTRADA_INVALIDA"
    assert rectangular.diagnostico.campo == "matriz_a"
    assert sin_datos.codigo == "ENTRADA_INVALIDA"
    assert "vacía" in sin_datos.diagnostico.mensaje


def test_filas_irregulares_se_rechazan_antes_de_leer_celdas() -> None:
    """Una cuadrícula con filas desiguales no llega al cálculo."""
    irregular = [[1], [0, 1]]
    resultado = resolver_jacobi(_entrada(irregular, [1, 1], [0, 0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.fila == 1
    assert "fila 1" in resultado.diagnostico.mensaje.lower()


@pytest.mark.parametrize("campo,vector_b,vector_inicial", [
    ("vector_b", [1], [0, 0]),
    ("vector_inicial", [1, 1], [0]),
])
def test_vector_incompleto_identifica_el_campo(campo, vector_b, vector_inicial) -> None:
    """Cada vector debe tener una componente por ecuación."""
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), vector_b, vector_inicial)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == campo


@pytest.mark.parametrize("vector_b", ["22", None, {"a": 1}])
def test_vector_con_contenedor_invalido_se_rechaza(vector_b) -> None:
    """Solo se admiten tuplas o listas como vectores."""
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), vector_b, [0, 0])
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"


@pytest.mark.parametrize("tolerancia", [0, Fraction(-1, 100), True, "0", "-1/3"])
def test_tolerancia_no_positiva_se_rechaza(tolerancia) -> None:
    """La tolerancia debe ser un racional estrictamente positivo."""
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), [2, 2], [0, 0], tolerancia)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "tolerancia"


@pytest.mark.parametrize("maximo", [True, 0, 101, 1.5, "2"])
def test_maximo_fuera_de_rango_se_rechaza(maximo) -> None:
    """El máximo es un entero positivo dentro del tope documentado."""
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), [2, 2], [0, 0], maximo=maximo)
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "maximo_iteraciones"


def test_division_por_cero_y_booleano_se_ubican() -> None:
    """Los valores inválidos informan su coordenada sin llegar a dividir."""
    division = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), ["1/0", 2], [0, 0])
    )
    booleano = resolver_jacobi(_entrada([[True]], [1], [0]))

    assert division.codigo == "ENTRADA_INVALIDA"
    assert division.diagnostico.fila == 1
    assert booleano.codigo == "ENTRADA_INVALIDA"
    assert (booleano.diagnostico.fila, booleano.diagnostico.columna) == (1, 1)


def test_valores_no_finitos_y_cadenas_largas_se_rechazan() -> None:
    """Los flotantes no finitos y las cadenas fuera de límite se rechazan."""
    no_finito = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), [float("nan"), 2], [0, 0])
    )
    larga = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), ["9" * 257, 2], [0, 0])
    )

    assert no_finito.codigo == "ENTRADA_INVALIDA"
    assert larga.codigo == "ENTRADA_INVALIDA"
    assert larga.diagnostico.campo == "vector_b"


def test_fraccion_demasiado_grande_se_rechaza() -> None:
    """El tamaño de numerador y denominador se acota antes de iterar."""
    enorme = Fraction(10 ** 5000)
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[4, 1], [1, 3]]), [enorme, 2], [0, 0])
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.fila == 1


def test_dominancia_estricta_se_informa_sin_bloquear() -> None:
    """Una matriz no dominante puede ejecutarse y su diagnóstico queda disponible."""
    dominante = _matriz_cuadrada([[4, 1], [1, 3]])
    no_dominante = _matriz_cuadrada([[1, 2], [0, 1]])
    resultado_dominante = resolver_jacobi(_entrada(dominante, [2, 2], [0, 0]))
    resultado_no_dominante = resolver_jacobi(_entrada(no_dominante, [3, 1], [0, 0]))

    assert resultado_dominante.dominancia_estricta is True
    assert resultado_no_dominante.dominancia_estricta is False
    assert resultado_no_dominante.codigo == "SOLUCION_EXACTA"


def test_las_entradas_no_se_modifican() -> None:
    """El cálculo usa una instantánea y conserva A, b y el vector inicial."""
    matriz = [[4, 1], [1, 3]]
    vector_b = [Fraction(2), Fraction(2)]
    vector_inicial = [Fraction(0), Fraction(0)]
    datos_originales = [fila[:] for fila in matriz]

    resolver_jacobi(_entrada(matriz, vector_b, vector_inicial, maximo=2))

    assert matriz == datos_originales
    assert vector_b == [Fraction(2), Fraction(2)]
    assert vector_inicial == [Fraction(0), Fraction(0)]


def test_entrada_ajena_al_contrato_se_rechaza() -> None:
    """El punto de entrada devuelve un diagnóstico si no recibe EntradaJacobi."""
    resultado = resolver_jacobi(object())

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.aproximacion is None
    assert resultado.diagnostico.campo == "entrada"


def test_flotante_pequeno_no_se_redondea_a_cero() -> None:
    """Un flotante no es un valor exacto, aunque el texto decimal sí lo sea."""
    flotante = resolver_jacobi(_entrada(_matriz_cuadrada([[1]]), [1e-8], [0]))
    exacto = resolver_jacobi(_entrada(
        _matriz_cuadrada([[1]]), ["0.00000001"], [0], Fraction(1, 10 ** 10),
    ))

    assert flotante.codigo == "ENTRADA_INVALIDA"
    assert flotante.diagnostico.campo == "vector_b"
    assert exacto.codigo == "SOLUCION_EXACTA"
    assert exacto.aproximacion == (Fraction(1, 10 ** 8),)


def test_la_longitud_cruda_se_comprueba_antes_de_limpiar() -> None:
    """Una cadena larga no se admite aunque sus espacios se recorten."""
    larga = " " * 300 + "1"
    resultado = resolver_jacobi(_entrada(_matriz_cuadrada([[1]]), [larga], [0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"


def test_vector_que_cambia_al_copiarse_se_rechaza() -> None:
    """La longitud se comprueba sobre una copia inmutable del vector."""
    class _VectorInestable(list):
        """Lista que declara dos componentes y entrega una al iterarse."""

        def __len__(self):
            self.consultas = getattr(self, "consultas", 0) + 1
            return 2 if self.consultas == 1 else 1

        def __iter__(self):
            return iter([list.__getitem__(self, 0)])

    vector_b = _VectorInestable([1, 1])
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[1, 0], [0, 1]]), vector_b, [0, 0])
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"


def test_la_matriz_inmutable_es_admisible() -> None:
    """El resolutor admite datos matriciales almacenados en tuplas de solo lectura."""
    matriz = ((2, 0), (0, 2))
    resultado = resolver_jacobi(_entrada(matriz, [4, 4], [0, 0]))

    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (Fraction(2), Fraction(2))


def test_la_dominancia_se_informa_en_fallos_posteriores() -> None:
    """Una matriz válida ya evaluable informa su dominancia aunque falle b."""
    resultado = resolver_jacobi(_entrada(_matriz_cuadrada([[1, 2], [0, 1]]), [1], [0, 0]))

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"
    assert resultado.dominancia_estricta is False


def test_la_matriz_se_lee_una_sola_vez() -> None:
    """Los cambios tras recorrer una cuadrícula no alteran la instantánea."""
    class _CuadriculaInestable(list):
        """Lista que devuelve ceros después del primer recorrido."""

        lecturas = 0

        def __iter__(self):
            self.lecturas += 1
            if self.lecturas == 1:
                return super().__iter__()
            return iter([[0, 0], [0, 0]])

    matriz = _CuadriculaInestable([[2, 0], [0, 2]])
    resultado = resolver_jacobi(_entrada(matriz, [4, 4], [0, 0]))

    assert matriz.lecturas == 1
    assert resultado.codigo == "SOLUCION_EXACTA"
    assert resultado.aproximacion == (Fraction(2), Fraction(2))


@pytest.mark.parametrize("valor", [object(), complex(1, 2), [1], {"a": 1}])
def test_tipos_ajenos_se_rechazan(valor) -> None:
    """Los tipos fuera del contrato se rechazan sin filtrar sus nombres internos."""
    resultado = resolver_jacobi(
        _entrada(_matriz_cuadrada([[1, 0], [0, 1]]), [valor, 1], [0, 0])
    )

    assert resultado.codigo == "ENTRADA_INVALIDA"
    assert resultado.diagnostico.campo == "vector_b"
    assert (resultado.diagnostico.fila, resultado.diagnostico.columna) == (1, None)
