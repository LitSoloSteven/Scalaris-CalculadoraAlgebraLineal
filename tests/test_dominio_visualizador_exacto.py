"""Caracterización exacta del escalamiento, las sumas y los planos degenerados."""
from fractions import Fraction
import json

import pytest

from src.backend.geometria.cadena_combinacion import calcular_cadena_acumulada
from src.backend.geometria.clasificacion import clasificar_ecuacion
from src.backend.geometria.conjunto_solucion import ConjuntoSolucion, TipoSolucionGeometria
from src.backend.geometria.cuadros_vectores import calcular_cuadros_vectores, calcular_suma_vectores
from src.backend.geometria.planos import calcular_geometria_plano
from src.backend.modelos.matriz import Matriz
from src.frontend.controladores.geometria import ControladorGeometria


@pytest.mark.parametrize("indice", range(-12, 13))
@pytest.mark.parametrize("dimension", [2, 3])
def test_cada_cuadro_conserva_escalar_y_coordenadas_exactas(indice, dimension):
    """Los 25 escalares mantienen incrementos de 1/4 y operaciones con Fraction."""
    primero = [Fraction(1, 1001), Fraction(-2, 1009), Fraction(3, 1013)][:dimension]
    segundo = [Fraction(-5, 1009), Fraction(7, 1001), Fraction(11, 1013)][:dimension]
    cuadros = calcular_cuadros_vectores(primero, segundo)
    cuadro = cuadros[indice + 12]
    escalar = Fraction(indice, 4)
    assert len(cuadros) == 25
    assert cuadro.escalar == escalar
    assert cuadro.vector_escalado == tuple(escalar * valor for valor in primero)
    assert cuadro.suma == tuple(escalar * valor + otro for valor, otro in zip(primero, segundo))
    assert all(isinstance(valor, Fraction) for valor in cuadro.vector_escalado + cuadro.suma)
    assert primero == [Fraction(1, 1001), Fraction(-2, 1009), Fraction(3, 1013)][:dimension]


def test_cancelacion_de_enteros_de_ochenta_cifras_antes_de_convertir():
    """La suma cancela dígitos grandes exactamente antes de producir flotantes."""
    grande = Fraction(int("9" * 80))
    primero = [grande, -grande]
    segundo = [1 - grande, grande + Fraction(1, 1009)]
    assert calcular_suma_vectores(primero, segundo) == [Fraction(1), Fraction(1, 1009)]
    cuadro = calcular_cuadros_vectores(primero, segundo)[16]
    assert cuadro.escalar == 1
    assert cuadro.suma == (Fraction(1), Fraction(1, 1009))
    carga = {"vectores": [{"datos": list(map(str, primero))}, {"datos": list(map(str, segundo))}]}
    resultado = ControladorGeometria.procesar_vectores(json.dumps(carga))
    assert resultado["estado"] == "EXITO"
    assert resultado["estatica"]["u_mas_v"] == [1.0, float(Fraction(1, 1009))]
    assert resultado["cuadros"][16]["escalar_por_u_mas_v"] == resultado["estatica"]["u_mas_v"]


def test_cadena_acumulada_conserva_fracciones_y_etiquetas():
    """Las sumas parciales preservan el orden de generadores y sus textos visibles."""
    columnas = [Matriz(2, 1, [[1], [2]]), Matriz(2, 1, [[-3], [4]])]
    cadena = calcular_cadena_acumulada({"coeficientes": [Fraction(1, 3), Fraction(-2, 5)]}, columnas, 2)
    assert [paso.coordenadas for paso in cadena] == [
        (Fraction(1, 3), Fraction(2, 3)), (Fraction(23, 15), Fraction(-14, 15)),
    ]
    assert [paso.etiqueta for paso in cadena] == ["c_1·v_1", "+ c_2·v_2"]


def test_cadena_cancela_enteros_de_ochenta_cifras_exactamente():
    """La última suma parcial mantiene una unidad pese a cancelar enteros grandes."""
    grande = Fraction(int("8" * 80))
    columnas = [Matriz(2, 1, [[grande], [-grande]]), Matriz(2, 1, [[1 - grande], [grande + 1]])]
    cadena = calcular_cadena_acumulada({"coeficientes": [Fraction(1), Fraction(1)]}, columnas, 2)
    assert cadena[0].coordenadas == (grande, -grande)
    assert cadena[1].coordenadas == (Fraction(1), Fraction(1))
    assert all(isinstance(valor, Fraction) for paso in cadena for valor in paso.coordenadas)


@pytest.mark.parametrize("coeficientes,esperado", [
    (["1/1001", "-2/1009"], (Fraction(7015, 1010009), Fraction(-5990, 1010009))),
    (["incorrecto", "1"], (Fraction(-3), Fraction(4))),
    ([], None),
])
def test_alternativa_textual_y_cadena_vacia_conservan_comportamiento(coeficientes, esperado):
    """Los coeficientes textuales, inválidos y vacíos conservan la regla histórica."""
    columnas = [Matriz(2, 1, [[1], [2]]), Matriz(2, 1, [[-3], [4]])]
    cadena = calcular_cadena_acumulada({"coeficientes_texto": coeficientes}, columnas, 2)
    if esperado is None:
        assert cadena == []
    else:
        assert cadena[-1].coordenadas == esperado


@pytest.mark.parametrize("direcciones", [
    [[0, 0, 0], [1, 2, 3]], [[1, 2, 3], [2, 4, 6]], [[1, 0, 0], [0, 0, 0]],
])
def test_plano_con_generadores_degenerados_conserva_normal_nula(direcciones):
    """Generadores dependientes conservan normal y desplazamiento exactos nulos."""
    exactas = [[Fraction(valor) for valor in direccion] for direccion in direcciones]
    normal, desplazamiento = calcular_geometria_plano(exactas, [Fraction(1, 1001)] * 3)
    assert normal == (Fraction(0), Fraction(0), Fraction(0))
    assert desplazamiento == Fraction(0)
    assert all(isinstance(valor, Fraction) for valor in normal)


@pytest.mark.parametrize("termino,tipo,estado,dimension", [
    ("0", "trivial", "SOLUCIONES_INFINITAS", 3),
    ("5", "contradiccion", "SIN_SOLUCION", 0),
])
def test_ecuacion_nula_tridimensional_conserva_solucion(termino, tipo, estado, dimension):
    """Un plano degenerado preserva el espacio completo o la incompatibilidad."""
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps({
        "matriz_a": [["0", "0", "0"]], "vector_b": [termino],
    }))
    assert resultado["estado"] == "EXITO"
    assert resultado["ecuaciones"][0]["tipo"] == tipo
    assert resultado["estado_solucion"] == estado
    assert resultado["conjunto_solucion"]["dimension"] == dimension
    assert resultado["conjunto_solucion"]["espacio_completo"] is (dimension == 3)


def test_enum_y_conjunto_no_publican_alias():
    """El enum publica cinco miembros y el conjunto solo sus propiedades canónicas."""
    assert {nombre: miembro.value for nombre, miembro in TipoSolucionGeometria.__members__.items()} == {
        "VACIA": "VACIA", "PUNTO": "PUNTO", "RECTA": "RECTA", "PLANO": "PLANO", "ESPACIO_AFIN": "ESPACIO_AFIN",
    }
    conjunto = ConjuntoSolucion(TipoSolucionGeometria.PUNTO, 0, (Fraction(1),), ())
    assert not any(hasattr(conjunto, nombre) for nombre in ("kind", "point", "directions"))


def test_modulo_conjunto_no_publica_funciones_o_clases_alternativas():
    """Las funciones y clases retiradas no quedan disponibles como alias."""
    from src.backend.geometria import conjunto_solucion
    retirados = (
        "SolutionKind", "SolutionSet", "classify", "has_solution_param", "get_solution_param",
        "from_solution_param", "from_gauss_result",
    )
    assert not any(hasattr(conjunto_solucion, nombre) for nombre in retirados)


@pytest.mark.parametrize("dimension,tipo", [(2, "recta"), (3, "plano")])
def test_clasificacion_no_nula_usa_valores_espanoles(dimension, tipo):
    """La clasificación no nula conserva la dimensión usando su valor canónico."""
    assert clasificar_ecuacion([Fraction(1)] * dimension, Fraction(2), dimension) == tipo
