"""Analisis exacto de conjuntos descritos por ecuaciones lineales."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.captura_subespacios import (
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.subespacios import analizar_subespacio


def _analizar(matriz_a, vector_b):
    """Construye la captura del sistema y devuelve el resultado del dominio."""
    return analizar_subespacio(capturar_restricciones({
        "modo": "restricciones",
        "dimension_ambiente": len(matriz_a[0]),
        "matriz_a": matriz_a,
        "vector_b": vector_b,
    }))


def test_sistema_homogeneo_describe_el_nucleo_con_base_exacta():
    """A x = 0 con A = [1 1 1] tiene rango uno, nulidad dos y la base esperada."""
    resultado = _analizar([[1, 1, 1]], [0])
    assert resultado["estado"] == "EXITO"
    assert resultado["codigo"] == "NUCLEO_HOMOGENEO"
    assert resultado["clasificacion"] == "SUBESPACIO"
    assert resultado["rango"] == 1
    assert resultado["rango_aumentada"] == 1
    assert resultado["base"] == (
        (Fraction(-1), Fraction(1), Fraction(0)),
        (Fraction(-1), Fraction(0), Fraction(1)),
    )
    assert resultado["direcciones"] == resultado["base"]
    assert resultado["dimension"] == 2
    assert resultado["columnas_pivote"] == (0,)
    assert resultado["columnas_libres"] == (1, 2)
    assert resultado["es_subespacio"] is True
    assert resultado["contiene_origen"] is True
    assert resultado["es_vacio"] is False
    assert resultado["particular"] == (Fraction(0), Fraction(0), Fraction(0))


def test_sistema_afin_compatible_no_contiene_al_origen():
    """A x = b con A = [1 1] y b = 1 conserva particular, direccion y dimension afin."""
    resultado = _analizar([[1, 1]], [1])
    assert resultado["codigo"] == "AFIN_NO_CONTIENE_ORIGEN"
    assert resultado["clasificacion"] == "AFIN_NO_SUBESPACIO"
    assert resultado["particular"] == (Fraction(1), Fraction(0))
    assert resultado["direcciones"] == ((Fraction(-1), Fraction(1)),)
    assert resultado["dimension_afin"] == 1
    assert resultado["base"] is None
    assert resultado["dimension"] is None
    assert resultado["es_subespacio"] is False
    assert resultado["contiene_origen"] is False
    assert resultado["es_vacio"] is False
    assert resultado["testigo"]["tipo"] == "origen_no_pertenece"
    assert resultado["testigo"]["indice_fila"] == 0
    assert resultado["testigo"]["valor_izquierdo"] == 0
    assert resultado["testigo"]["termino_independiente"] == 1


def test_sistema_incompatible_es_vacio_y_conserva_testigo_contradictorio():
    """x = 1 y x = 2 no tienen solucion; el rango aumentado supera en uno al de A."""
    resultado = _analizar([[1, 0], [1, 0]], [1, 2])
    assert resultado["codigo"] == "SISTEMA_INCOMPATIBLE"
    assert resultado["clasificacion"] == "VACIO_NO_SUBESPACIO"
    assert resultado["rango"] == 1
    assert resultado["rango_aumentada"] == 2
    assert resultado["base"] is None
    assert resultado["dimension"] is None
    assert resultado["es_subespacio"] is False
    assert resultado["es_vacio"] is True
    assert resultado["testigo"]["tipo"] == "fila_contradictoria"
    assert resultado["testigo"]["indice_fila"] == 1
    assert resultado["testigo"]["coeficientes"] == (Fraction(0), Fraction(0))
    assert resultado["testigo"]["termino_independiente"] == 1
    assert resultado["testigo"]["valor_izquierdo"] == 0


def test_matriz_nula_con_b_nula_describe_todo_el_espacio():
    """A = 0 en dos por tres con b = 0 produce R^3 y su base canonica."""
    resultado = _analizar([[0, 0, 0], [0, 0, 0]], [0, 0])
    assert resultado["rango"] == 0
    assert resultado["dimension"] == 3
    assert resultado["base"] == (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )
    assert resultado["columnas_libres"] == (0, 1, 2)


def test_identidad_homogenea_describe_el_subespacio_cero():
    """A = I3 con b = 0 solo admite la solucion trivial, con base vacia."""
    resultado = _analizar([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0, 0, 0])
    assert resultado["rango"] == 3
    assert resultado["dimension"] == 0
    assert resultado["base"] == ()
    assert resultado["direcciones"] == ()
    assert resultado["es_subespacio"] is True
    assert resultado["es_vacio"] is False


def test_filas_redundantes_no_cambian_la_base_ni_la_dimension():
    """Repetir una ecuacion no altera el conjunto solucion ni sus indices pivote."""
    simple = _analizar([[1, 1]], [0])
    redundante = _analizar([[1, 1], [2, 2]], [0, 0])
    assert redundante["rango"] == simple["rango"]
    assert redundante["base"] == simple["base"]
    assert redundante["dimension"] == simple["dimension"]
    assert redundante["columnas_libres"] == simple["columnas_libres"]


def test_pivote_en_columna_media_y_final_excluye_la_columna_de_b():
    """El pivote se busca solo entre las variables y nunca en la columna de terminos."""
    media = _analizar([[0, 1, 0]], [0])
    final = _analizar([[0, 0, 1]], [0])
    assert media["columnas_pivote"] == (1,)
    assert media["base"] == (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )
    assert final["columnas_pivote"] == (2,)
    assert final["base"] == (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
    )


def test_fracciones_largas_se_conservan_sin_umbral_de_flotante():
    """Un denominador de un billon no se redondea ni se considera cero."""
    resultado = _analizar(
        [["1/3", "1/1000000000000"]],
        ["1/7"],
    )
    assert resultado["particular"] == (Fraction(3, 7), Fraction(0))
    assert resultado["direcciones"] == ((Fraction(-3, 1000000000000), Fraction(1)),)
    assert resultado["dimension_afin"] == 1


def test_sistema_afin_con_solucion_unica_tiene_dimension_afin_cero():
    """A = I2 con b distinto de cero es un punto afin, no un subespacio."""
    resultado = _analizar([[1, 0], [0, 1]], [2, 3])
    assert resultado["codigo"] == "AFIN_NO_CONTIENE_ORIGEN"
    assert resultado["particular"] == (Fraction(2), Fraction(3))
    assert resultado["direcciones"] == ()
    assert resultado["dimension_afin"] == 0
    assert resultado["base"] is None


def test_varias_filas_contradictorias_mantienen_rango_aumentado_una_unidad_mayor():
    """Aunque haya tres filas incompatibles, el rango aumentado es rango(A) + 1."""
    resultado = _analizar([[1, 0], [1, 0], [1, 0]], [1, 2, 3])
    assert resultado["rango"] == 1
    assert resultado["rango_aumentada"] == 2
    assert resultado["testigo"]["indice_fila"] == 1
    assert resultado["testigo"]["termino_independiente"] == 1


def test_restricciones_no_mutan_la_matriz_de_entrada():
    """La construccion de la matriz aumentada y la reduccion usan copias."""
    matriz = Matriz(1, 2, [[1, 1]])
    entrada = {
        "modo": "restricciones",
        "dimension_ambiente": 2,
        "matriz_a": matriz,
        "vector_b": (Fraction(1),),
    }
    antes = [fila[:] for fila in matriz.datos]
    resultado = analizar_subespacio(entrada)
    assert resultado["estado"] == "EXITO"
    assert matriz.datos == antes
