"""Analisis exacto de subespacios descritos por generadores."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.captura_subespacios import (
    capturar_generadores,
)
from src.backend.resolutores.operaciones_vectores.subespacios import analizar_subespacio


def _analizar(columnas, etiquetas=None):
    """Construye la captura de generadores y devuelve el resultado del dominio."""
    nombres = etiquetas or [f"v_{indice + 1}" for indice in range(len(columnas))]
    vectores = {
        nombre: {"datos": list(columna), "orientacion": "columna"}
        for nombre, columna in zip(nombres, columnas)
    }
    return analizar_subespacio(capturar_generadores({
        "modo": "generadores",
        "dimension_ambiente": len(columnas[0]),
        "vectores": vectores,
    }))


def test_generadores_dependientes_eligen_columnas_originales():
    """La base usa las columnas pivote de la matriz original, no las columnas reducidas."""
    resultado = _analizar([(1, 2, 3), (2, 4, 6), (0, 1, 1)])
    assert resultado["estado"] == "EXITO"
    assert resultado["codigo"] == "SUBESPACIO_GENERADO"
    assert resultado["clasificacion"] == "SUBESPACIO"
    assert resultado["rango"] == 2
    assert resultado["dimension"] == 2
    assert resultado["indices_generadores_base"] == (0, 2)
    assert resultado["etiquetas_generadores_base"] == ("v_1", "v_3")
    assert resultado["base"] == (
        (Fraction(1), Fraction(2), Fraction(3)),
        (Fraction(0), Fraction(1), Fraction(1)),
    )
    assert resultado["es_subespacio"] is True
    assert resultado["contiene_origen"] is True
    assert resultado["es_vacio"] is False
    assert resultado["rango_aumentada"] is None


def test_generadores_nulos_describen_el_subespacio_cero():
    """Dos generadores nulos producen base vacia y dimension cero, no una captura vacia."""
    resultado = _analizar([(0, 0, 0), (0, 0, 0)])
    assert resultado["rango"] == 0
    assert resultado["dimension"] == 0
    assert resultado["base"] == ()
    assert resultado["es_subespacio"] is True
    assert resultado["es_vacio"] is False
    assert resultado["columnas_pivote"] == ()
    assert resultado["columnas_libres"] == (0, 1)


@pytest.mark.parametrize("columnas,pivote,esperada", [
    ([(1, 0, 0), (0, 0, 0), (0, 0, 0)], 0, (1, 0, 0)),
    ([(0, 0, 0), (0, 1, 0), (0, 0, 0)], 1, (0, 1, 0)),
    ([(0, 0, 0), (0, 0, 0), (0, 1, 0)], 2, (0, 1, 0)),
])
def test_generadores_con_pivote_inicial_medio_y_final(columnas, pivote, esperada):
    """El indice pivote se conserva en la base original y en el orden de entrada."""
    resultado = _analizar(columnas)
    assert resultado["columnas_pivote"] == (pivote,)
    assert resultado["indices_generadores_base"] == (pivote,)
    assert resultado["base"] == (tuple(Fraction(valor) for valor in esperada),)


def test_generadores_respetan_etiquetas_y_orden_de_insercion():
    """Las etiquetas acompanan a las columnas originales y no se ordenan como texto."""
    resultado = _analizar(
        [(1, 1), (2, 2), (0, 1)],
        etiquetas=["v_10", "v_2", "v_1"],
    )
    assert resultado["etiquetas_generadores_base"] == ("v_10", "v_1")
    assert resultado["indices_generadores_base"] == (0, 2)
    assert resultado["columnas_libres"] == (1,)


def test_generadores_completos_conservan_la_base_original():
    """Una familia independiente no se transforma: se devuelven sus columnas de entrada."""
    resultado = _analizar([(1, 0, 0), (0, 1, 0), (0, 0, 1)])
    assert resultado["rango"] == 3
    assert resultado["dimension"] == 3
    assert resultado["indices_generadores_base"] == (0, 1, 2)
    assert resultado["base"] == (
        (Fraction(1), Fraction(0), Fraction(0)),
        (Fraction(0), Fraction(1), Fraction(0)),
        (Fraction(0), Fraction(0), Fraction(1)),
    )


def test_generadores_no_mutan_las_matrices_de_entrada():
    """La reduccion trabaja sobre copias y deja intacta la captura original."""
    originales = (Matriz(3, 1, [[1], [2], [3]]), Matriz(3, 1, [[2], [4], [6]]))
    entrada = {
        "modo": "generadores",
        "dimension_ambiente": 3,
        "generadores": originales,
        "etiquetas": ("a", "b"),
    }
    antes = [vector.datos for vector in originales]
    resultado = analizar_subespacio(entrada)
    assert resultado["estado"] == "EXITO"
    assert [vector.datos for vector in originales] == antes


def test_generadores_rechazan_vector_con_forma_irregular():
    """Un vector columna manipulado produce error de entrada con la ubicacion de su fila."""
    vector = Matriz(3, 1, [[1], [2], [3]])
    vector.datos.pop()
    resultado = analizar_subespacio({
        "modo": "generadores",
        "dimension_ambiente": 3,
        "generadores": (vector,),
        "etiquetas": ("v_1",),
    })
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert "generadores[0].datos" in resultado["mensaje"]


def test_generadores_dejan_traza_y_comprobaciones_exactas():
    """La traza es inmutable y cada comprobacion confirma columnas originales e independencia."""
    resultado = _analizar([(1, 2, 3), (2, 4, 6), (0, 1, 1)])
    assert isinstance(resultado["pasos"], tuple)
    assert resultado["pasos"]
    assert all(isinstance(paso["matriz"], Matriz) for paso in resultado["pasos"])
    assert isinstance(resultado["comprobaciones"], tuple)
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
    assert {comprobacion["tipo"] for comprobacion in resultado["comprobaciones"]} == {
        "columna_original", "independencia_base",
    }
