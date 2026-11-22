"""Captura exacta y acotada de generadores y restricciones de subespacios."""
from fractions import Fraction

import pytest

from src.backend.resolutores.operaciones_vectores.subespacios.captura_subespacios import (
    capturar_generadores,
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.subespacios.contrato_subespacios import (
    ErrorCapturaSubespacio,
)


def test_generadores_conservan_orden_etiquetas_y_fracciones():
    """Las etiquetas siguen el orden de insercion y las celdas se guardan como racionales."""
    captura = {
        "modo": "generadores",
        "dimension_ambiente": 3,
        "vectores": {
            "v_2": {"datos": ["1/3", "", 2], "orientacion": "columna"},
            "v_10": {"datos": [0, "1/1000000000000", -1], "orientacion": "columna"},
            "v_1": {"datos": [4, 5, 6], "orientacion": "columna"},
        },
    }
    entrada = capturar_generadores(captura)
    assert entrada["modo"] == "generadores"
    assert entrada["dimension_ambiente"] == 3
    assert entrada["etiquetas"] == ("v_2", "v_10", "v_1")
    assert [vector.filas for vector in entrada["generadores"]] == [3, 3, 3]
    assert entrada["generadores"][0].datos == [[Fraction(1, 3)], [Fraction(0)], [Fraction(2)]]
    assert entrada["generadores"][1].datos[1] == [Fraction(1, 1000000000000)]
    assert all(isinstance(valor, Fraction)
               for vector in entrada["generadores"] for fila in vector.datos for valor in fila)


@pytest.mark.parametrize("captura,codigo", [
    ({}, "CAMPOS_FALTANTES"),
    ({"modo": "generadores", "dimension_ambiente": 3}, "CAMPOS_FALTANTES"),
    ({"modo": "generadores", "dimension_ambiente": 3, "vectores": {}}, "CANTIDAD_INVALIDA"),
    ({"modo": "generadores", "dimension_ambiente": 0,
      "vectores": {"v_1": {"datos": [1]}}}, "DIMENSION_INVALIDA"),
    ({"modo": "generadores", "dimension_ambiente": 3,
      "vectores": {"v_1": {"datos": [1, 2, 3], "orientacion": "fila"}}},
     "ORIENTACION_INVALIDA"),
    ({"modo": "generadores", "dimension_ambiente": 3,
      "vectores": {"v_1": {"datos": [1, 2]}}}, "LONGITUD_INVALIDA"),
    ({"modo": "generadores", "dimension_ambiente": 3,
      "vectores": {"v_1": {"datos": [1, True, 3]}}}, "VALOR_BOOLEANO"),
    ({"modo": "generadores", "dimension_ambiente": 3,
      "vectores": {"v_1": {"datos": [1, "1/0", 3]}}}, "VALOR_INVALIDO"),
    ({"modo": "generadores", "dimension_ambiente": 3,
      "vectores": {"v_1": {"datos": [1, "nan", 3]}}}, "VALOR_INVALIDO"),
])
def test_generadores_rechazan_capturas_invalidas_con_ubicacion(captura, codigo):
    """Cada rechazo conserva un codigo estable y una ubicacion util, sin calculo parcial."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores(captura)
    assert error.value.codigo == codigo
    assert error.value.ubicacion


def test_generadores_rechazan_exceso_de_vectores():
    """El limite de diez generadores se aplica antes de convertir las celdas."""
    vectores = {f"v_{indice}": {"datos": [indice, 0, 0]} for indice in range(11)}
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores({
            "modo": "generadores", "dimension_ambiente": 3, "vectores": vectores,
        })
    assert error.value.codigo == "CANTIDAD_INVALIDA"


def test_restricciones_conservan_matriz_terminos_y_racionales():
    """A y b se convierten con el parser exacto, incluidas celdas vacias y fracciones largas."""
    captura = {
        "modo": "restricciones",
        "dimension_ambiente": 3,
        "matriz_a": [["1/3", "", 2], [0, "1/1000000000000", -1]],
        "vector_b": ["1/2", 0],
    }
    entrada = capturar_restricciones(captura)
    assert entrada["modo"] == "restricciones"
    assert entrada["dimension_ambiente"] == 3
    assert entrada["matriz_a"].filas == 2
    assert entrada["matriz_a"].columnas == 3
    assert entrada["matriz_a"].datos[0] == [Fraction(1, 3), Fraction(0), Fraction(2)]
    assert entrada["matriz_a"].datos[1][1] == Fraction(1, 1000000000000)
    assert entrada["vector_b"] == (Fraction(1, 2), Fraction(0))


@pytest.mark.parametrize("captura,codigo", [
    ({}, "CAMPOS_FALTANTES"),
    ({"modo": "restricciones", "dimension_ambiente": 2, "matriz_a": [], "vector_b": []},
     "FILAS_INVALIDAS"),
    ({"modo": "restricciones", "dimension_ambiente": 2,
      "matriz_a": [[1, 0], [0, 1], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6],
                   [7, 7], [8, 8], [9, 9]], "vector_b": [0] * 11}, "FILAS_INVALIDAS"),
    ({"modo": "restricciones", "dimension_ambiente": 2,
      "matriz_a": [[1, 0, 0]], "vector_b": [0]}, "FILA_INVALIDA"),
    ({"modo": "restricciones", "dimension_ambiente": 2,
      "matriz_a": [[1, 0]], "vector_b": [0, 1]}, "TERMINOS_INVALIDOS"),
    ({"modo": "restricciones", "dimension_ambiente": 2,
      "matriz_a": [[1, True]], "vector_b": [0]}, "VALOR_BOOLEANO"),
    ({"modo": "restricciones", "dimension_ambiente": 2,
      "matriz_a": [[1, "1/0"]], "vector_b": [0]}, "VALOR_INVALIDO"),
])
def test_restricciones_rechazan_formas_y_valores_invalidos(captura, codigo):
    """La captura rectangular valida filas, terminos y celdas antes de construir la matriz."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones(captura)
    assert error.value.codigo == codigo
    assert error.value.ubicacion


def test_restricciones_rechazan_campos_ajenos_y_dimension_excesiva():
    """No se aceptan claves no previstas ni dimensiones fuera del limite comun."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 2,
            "matriz_a": [[1, 0]], "vector_b": [0], "extra": True,
        })
    assert error.value.codigo == "CAMPOS_AJENOS"
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 11,
            "matriz_a": [[1] * 11], "vector_b": [0],
        })
    assert error.value.codigo == "DIMENSION_INVALIDA"


def test_generadores_rechazan_flotantes_aunque_sean_casi_cero():
    """Un flotante no se redondea en silencio: el dominio exige enteros o fracciones."""
    for celda in (0.0, 1e-7, 1.5):
        with pytest.raises(ErrorCapturaSubespacio) as error:
            capturar_generadores({
                "modo": "generadores", "dimension_ambiente": 1,
                "vectores": {"v_1": {"datos": [celda]}},
            })
        assert error.value.codigo == "VALOR_NO_EXACTO"
        assert error.value.ubicacion == "vectores.v_1.datos[0]"


def test_restricciones_rechazan_flotantes_aunque_sean_casi_cero():
    """La misma politica exacta se aplica a A y b en el modo de restricciones."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 1,
            "matriz_a": [[1e-7]], "vector_b": [0],
        })
    assert error.value.codigo == "VALOR_NO_EXACTO"
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 1,
            "matriz_a": [[0]], "vector_b": [0.5],
        })
    assert error.value.codigo == "VALOR_NO_EXACTO"


def test_captura_rechaza_un_modo_distinto_al_de_la_funcion():
    """Cada funcion de captura exige el modo que declara para no analizar otra forma."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores({
            "modo": "restricciones", "dimension_ambiente": 1,
            "vectores": {"v_1": {"datos": [1]}},
        })
    assert error.value.codigo == "MODO_INVALIDO"
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "generadores", "dimension_ambiente": 1,
            "matriz_a": [[1]], "vector_b": [0],
        })
    assert error.value.codigo == "MODO_INVALIDO"


@pytest.mark.parametrize("etiqueta", ["x" * 65, "a\x00b", "a\u200bb", "   "])
def test_generadores_rechazan_etiquetas_largas_vacias_o_invisibles(etiqueta):
    """Las etiquetas se acotan a 64 caracteres visibles para no inflar el resultado."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores({
            "modo": "generadores", "dimension_ambiente": 1,
            "vectores": {etiqueta: {"datos": [1]}},
        })
    assert error.value.codigo == "ETIQUETA_INVALIDA"


def test_campos_ajenos_resumen_las_claves_sin_volcarlas_todas():
    """Un mapa con muchas claves ajenas produce un mensaje acotado y determinista."""
    captura = {"modo": "generadores", "dimension_ambiente": 1,
               "vectores": {"v_1": {"datos": [1]}}}
    captura.update({f"extra_{indice}": indice for indice in range(20)})
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores(captura)
    assert error.value.codigo == "CAMPOS_AJENOS"
    assert "y 15 mas" in str(error.value)


def test_captura_rechaza_celdas_de_texto_excesivas_antes_de_interpretarlas():
    """El limite se aplica al texto crudo, aunque solo contenga espacios."""
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 1,
            "matriz_a": [[" " * 10_000]], "vector_b": [0],
        })
    assert error.value.codigo == "VALOR_INVALIDO"
    assert error.value.ubicacion == "matriz_a[0][0]"
    with pytest.raises(ErrorCapturaSubespacio) as error:
        capturar_generadores({
            "modo": "generadores", "dimension_ambiente": 1,
            "vectores": {"v_1": {"datos": [" " * 10_000]}},
        })
    assert error.value.codigo == "VALOR_INVALIDO"
    assert error.value.ubicacion == "vectores.v_1.datos[0]"


def test_celdas_breves_en_blanco_siguen_valiendo_cero():
    """Una celda vacia o de espacios cortos dentro de un ejercicio explicito es cero."""
    entrada = capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 1,
        "matriz_a": [["   "]], "vector_b": [""],
    })
    assert entrada["matriz_a"].datos == [[Fraction(0)]]
    assert entrada["vector_b"] == (Fraction(0),)
