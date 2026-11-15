"""Captura exacta y acotada de generadores y restricciones de subespacios."""
from fractions import Fraction

import pytest

from src.backend.resolutores.operaciones_vectores.captura_subespacios import (
    capturar_generadores,
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.contrato_subespacios import (
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
