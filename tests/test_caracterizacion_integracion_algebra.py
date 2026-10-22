"""Invariantes conjuntas de determinantes, reduccion y sistemas homogeneos."""
from fractions import Fraction
import json

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante import ResolutorDeterminante
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan
from src.backend.utilidades.verificacion import verificar_solucion
from src.frontend.controladores.sistemas_lineales.controlador_gauss import ControladorGauss
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import ControladorGaussJordan


@pytest.mark.parametrize("metodo", [
    ResolutorDeterminante.resolver_laplace, ResolutorDeterminante.resolver_lu,
])
@pytest.mark.parametrize("datos,esperado", [
    ([[Fraction(1, 10**12)]], Fraction(1, 10**12)),
    ([[Fraction(1, 2), Fraction(1, 3)], [Fraction(2, 5), Fraction(3, 7)]], Fraction(17, 210)),
    ([[2, 3, 1], [4, 1, -3], [1, 2, 0]], Fraction(10)),
    ([[1, 2, 3], [0, 0, 0], [4, 5, 6]], Fraction(0)),
    ([[0, 1, 2], [0, 3, 4], [0, 5, 7]], Fraction(0)),
    ([[0, 1, 0], [1, 0, 0], [0, 0, 1]], Fraction(-1)),
    ([[0, 1, 0], [0, 0, 1], [1, 0, 0]], Fraction(1)),
])
def test_determinantes_conservan_valor_signo_y_entrada(metodo, datos, esperado):
    """Ambos metodos respetan valores conocidos y no modifican la matriz recibida."""
    matriz = Matriz(len(datos), len(datos[0]), datos)
    original = tuple(tuple(fila) for fila in matriz.datos)
    resultado = metodo(matriz)
    assert resultado["determinante"] == esperado
    assert isinstance(resultado["determinante"], Fraction)
    assert resultado["es_singular"] is (esperado == 0)
    assert tuple(tuple(fila) for fila in matriz.datos) == original


@pytest.mark.parametrize("resolutor", [ResolutorGauss, ResolutorGaussJordan])
def test_bloques_independientes_no_se_convierten_en_pivotes(resolutor):
    """Tres columnas independientes no aumentan el rango del bloque coeficiente."""
    matriz = Matriz(2, 5, [[1, 2, 0, 1, 100], [3, 6, 1, 0, -100]])
    resultado = resolutor(matriz, numero_terminos_independientes=3).resolver_reduccion()
    assert resultado["rango"] == 1
    assert resultado["columnas_pivote"] == [0]
    assert resultado["matriz_reducida"].datos == [
        [Fraction(1), Fraction(2), Fraction(1, 3), Fraction(0), Fraction(-100, 3)],
        [Fraction(0), Fraction(0), Fraction(-1, 3), Fraction(1), Fraction(400, 3)],
    ]


def _comprobar_nucleo(coeficientes, direcciones):
    ceros = [Fraction(0)] * len(coeficientes)
    for direccion in direcciones:
        correcto, detalle = verificar_solucion(coeficientes, direccion, ceros)
        assert correcto, detalle


def _comprobar_bases_equivalentes(direcciones, base_transformacion, libres):
    assert len(base_transformacion) == len(direcciones)
    if not libres:
        return
    coordenadas = [[vector[columna] for columna in libres] for vector in base_transformacion]
    matriz = Matriz(len(libres), len(libres), coordenadas)
    assert ResolutorDeterminante.resolver_lu(matriz)["determinante"] != 0
    for vector in base_transformacion:
        reconstruido = [
            sum(vector[columna] * direccion[indice]
                for columna, direccion in zip(libres, direcciones))
            for indice in range(len(vector))
        ]
        assert reconstruido == vector


@pytest.mark.parametrize("coeficientes,rango_esperado", [
    ([[0, 1, 2], [0, 2, 5]], 2),
    ([[1, 2, 0, 1], [2, 4, 0, 2]], 1),
    ([[0, 0], [0, 0]], 0),
    ([[0, 2], [3, 0], [0, 0]], 2),
    ([[Fraction(1, 2), Fraction(1, 3), Fraction(5, 7)],
      [Fraction(3, 2), 1, Fraction(15, 7)]], 1),
])
def test_homogeneos_y_transformaciones_comparten_espacio_nulo(coeficientes, rango_esperado):
    """Rango, dependencia y bases describen el mismo nucleo con columnas libres iniciales."""
    filas, columnas = len(coeficientes), len(coeficientes[0])
    aumentada = Matriz(filas, columnas + 1, [fila + [0] for fila in coeficientes])
    sistema = ResolutorGauss(aumentada).resolver()
    transformacion = ResolutorTransformacionesLineales().resolver(Matriz(filas, columnas, coeficientes))
    parametrica = sistema["parametros_solucion"]
    direcciones = parametrica["direcciones"]
    base_transformacion = [[Fraction(valor) for valor in vector["vector"]]
                          for vector in transformacion["base_nucleo"]]
    assert sistema["analisis_sistema"]["es_homogeneo"] is True
    assert sistema["analisis_sistema"]["rango_a"] == transformacion["rango"] == rango_esperado
    assert transformacion["nulidad"] == len(direcciones) == columnas - rango_esperado
    assert parametrica["particular"] == [Fraction(0)] * columnas
    independencia = sistema["analisis_sistema"]["dependencia_lineal"]
    assert independencia["son_linealmente_independientes"] is (rango_esperado == columnas)
    _comprobar_nucleo(coeficientes, direcciones + base_transformacion)
    _comprobar_bases_equivalentes(direcciones, base_transformacion, sistema["columnas_libres"])


@pytest.mark.parametrize("controlador", [ControladorGauss, ControladorGaussJordan])
def test_consumidores_serializan_relaciones_homogeneas_exactas(controlador):
    """La respuesta publica conserva homogeneidad y coeficientes racionales del nucleo."""
    carga = {"matriz_a": [["0", "2", "3"]], "vector_b": ["0"]}
    resultado = json.loads(controlador.procesar_sistema(json.dumps(carga)))
    parametrica = resultado["parametros_solucion"]
    assert resultado["estado"] == "SOLUCIONES_INFINITAS"
    assert resultado["analisis_sistema"]["es_homogeneo"] is True
    assert parametrica["columnas_libres"] == [0, 2]
    assert [[Fraction(valor) for valor in direccion] for direccion in parametrica["direcciones"]] == [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(-3, 2), Fraction(1)],
    ]
