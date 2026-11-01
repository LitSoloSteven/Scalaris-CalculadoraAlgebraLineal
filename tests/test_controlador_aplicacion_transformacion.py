"""Contrato de frontend para aplicar y comprobar transformaciones exactas."""
import json
from unittest.mock import patch

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_MODELOS, LONGITUD_MAXIMA_CADENA_NUMERO
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.frontend.controladores.operaciones_matrices.controlador_aplicacion_transformacion import (
    ControladorAplicacionTransformacion,
)
from src.frontend.controladores.operaciones_matrices.controlador_transformaciones import ControladorTransformaciones


def _procesar(matriz: object, vector: object) -> dict:
    carga = json.dumps({"matriz_transformacion": matriz, "vector_original": vector})
    return json.loads(ControladorAplicacionTransformacion.procesar(carga))


@pytest.mark.parametrize("matriz,vector,esperado", [
    ([[1, 0], [0, 1]], [3, 4], ["3", "4"]),
    ([[2, 0], [0, 3]], [3, 4], ["6", "12"]),
    ([[1, 0], [0, -1]], [3, 4], ["3", "-4"]),
    ([[0, -1], [1, 0]], [3, 4], ["-4", "3"]),
    ([[2, 1], [1, 3]], ["1/2", "1/3"], ["4/3", "3/2"]),
    ([["0.1", "0.2"]], ["0.1", "0.2"], ["1/20"]),
    ([[1, 2], [3, 4], [5, 6]], [1, -1], ["-1", "-1", "-1"]),
    ([[1, 2, 3], [4, 5, 6]], [1, 0, -1], ["-2", "-2"]),
    ([[0, 0], [0, 0]], ["3/7", "-1/5"], ["0", "0"]),
    ([[7]], ["2/7"], ["2"]),
])
def test_aplicacion_con_resultado_y_comprobacion_exactos(matriz, vector, esperado):
    """Conserva racionales y desarrolla Av=y para cada componente de salida."""
    resultado = _procesar(matriz, vector)
    assert resultado["estado"] == "EXITO"
    assert resultado["vector_transformado"]["exacta"] == esperado
    assert resultado["verificacion"] is True
    assert resultado["aproximacion"] is False
    assert resultado["dimension_dominio"] == len(vector)
    assert resultado["dimension_codominio"] == len(esperado)
    assert len(resultado["pasos"]) == len(esperado)
    assert len(resultado["traza_comprobacion"]) == len(esperado) + 2
    assert all(paso["tipo"] == "verificacion" for paso in resultado["traza_comprobacion"])
    assert "coincide" in resultado["traza_comprobacion"][-1]["descripcion"]


def test_contrato_contiene_matriz_estructurada_y_coordenadas_graficas():
    """Serializa A sin convertir objetos Matriz a representaciones de Python."""
    resultado = _procesar([["1/3", 0], [0, 1]], ["1/2", 3])
    assert resultado["matriz_a"] == {"filas": 2, "columnas": 2, "datos": [["1/3", "0"], ["0", "1"]]}
    assert resultado["vector_original"] == {"exacta": ["1/2", "3"], "aproximado": [0.5, 3.0]}
    assert resultado["vector_transformado"]["aproximado"] == [1 / 6, 3.0]
    json.dumps(resultado, allow_nan=False)


@pytest.mark.parametrize("carga", ["{", "[]", "null", '"texto"', "1"])
def test_carga_json_invalida_devuelve_error(carga):
    """Rechaza sintaxis incorrecta y cargas que no representan un objeto."""
    resultado = json.loads(ControladorAplicacionTransformacion.procesar(carga))
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"]


@pytest.mark.parametrize("matriz,vector,fragmento", [
    (None, [1], "matriz A"),
    ([], [1], "matriz A"),
    ("A", [1], "matriz A"),
    ([1], [1], "Fila 1"),
    ([[]], [1], "dimensiones deben ser positivas"),
    ([[1, 2], [3]], [1, 2], "Fila 2"),
    ([[1]], None, "vector original"),
    ([[1]], [], "vector original"),
    ([[1]], "1", "vector original"),
    ([[1]], [[1]], "v[1,1]"),
    ([[1]], [""], "v[1,1]"),
    ([["1/0"]], [1], "A[1,1]"),
    ([[1]], ["abc"], "v[1,1]"),
    ([[1]], ["NaN"], "v[1,1]"),
    ([[1]], ["Infinity"], "v[1,1]"),
    ([[1]], ["1e3"], "v[1,1]"),
    ([[1, 0], [0, 1]], [1], "Dimensiones incompatibles"),
    ([[1]], ["9" * (LONGITUD_MAXIMA_CADENA_NUMERO + 1)], "v[1,1]"),
])
def test_entradas_invalidas_conservan_error_del_dominio(matriz, vector, fragmento):
    """Informa estructura, celda o dimensión inválida sin devolver un falso éxito."""
    resultado = _procesar(matriz, vector)
    assert resultado["estado"] == "ERROR"
    assert fragmento in resultado["mensaje"]
    assert "verificacion" not in resultado


def test_resultado_fuera_de_rango_grafico_conserva_valor_exacto():
    """Mantiene el cálculo racional si la coordenada no cabe en un flotante."""
    exponente = LONGITUD_MAXIMA_CADENA_NUMERO - 1
    componente = "1" + "0" * exponente
    resultado = _procesar([[componente]], [componente])
    assert resultado["estado"] == "EXITO"
    assert resultado["vector_transformado"]["exacta"] == ["1" + "0" * (2 * exponente)]
    assert resultado["vector_transformado"]["aproximado"] == [None]
    assert resultado["verificacion"] is True
    json.dumps(resultado, allow_nan=False)


def test_limite_de_modelos_admite_dimension_maxima():
    """Aplica una identidad del tamaño máximo vigente sin recortar coordenadas."""
    dimension = DIMENSION_MAXIMA_MODELOS
    matriz = [[int(fila == columna) for columna in range(dimension)] for fila in range(dimension)]
    resultado = _procesar(matriz, list(range(dimension)))
    assert resultado["vector_transformado"]["exacta"] == [str(indice) for indice in range(dimension)]
    assert resultado["verificacion"] is True


@pytest.mark.parametrize("matriz,vector", [
    ([[1]] * (DIMENSION_MAXIMA_MODELOS + 1), [1]),
    ([[1] * (DIMENSION_MAXIMA_MODELOS + 1)], [1]),
    ([[1]], [1] * (DIMENSION_MAXIMA_MODELOS + 1)),
])
def test_limites_superados_producen_error(matriz, vector):
    """Impide cargas mayores que los límites compartidos del dominio."""
    resultado = _procesar(matriz, vector)
    assert resultado["estado"] == "ERROR"
    assert "hasta" in resultado["mensaje"]


def test_aplicacion_delega_el_producto_en_el_resolutor():
    """Comprueba que el controlador usa el resolutor y conserva sus pasos."""
    original = ResolutorTransformacionesLineales.aplicar
    with patch.object(ResolutorTransformacionesLineales, "aplicar", autospec=True, side_effect=original) as aplicar:
        resultado = _procesar([[2]], [3])
    aplicar.assert_called_once()
    assert resultado["vector_transformado"]["exacta"] == ["6"]
    assert resultado["pasos"]


def test_comprobacion_detecta_resultado_incorrecto():
    """No certifica un valor adulterado aunque la aplicación indique éxito."""
    original = ResolutorTransformacionesLineales.aplicar

    def adulterar_resultado(resolutor, matriz, vector):
        resultado = original(resolutor, matriz, vector)
        resultado["vector_transformado"]["exacta"] = ["999"]
        return resultado

    with patch.object(ResolutorTransformacionesLineales, "aplicar", autospec=True, side_effect=adulterar_resultado):
        resultado = _procesar([[2]], [3])
    assert resultado["verificacion"] is False
    assert "no coincide" in resultado["traza_comprobacion"][-1]["descripcion"]


def test_error_del_resolutor_no_se_certifica():
    """Conserva un error de dominio sin intentar construir comprobaciones."""
    error = {"estado": "ERROR", "mensaje": "No se pudo aplicar la transformación."}
    with patch.object(ResolutorTransformacionesLineales, "aplicar", return_value=error):
        assert _procesar([[1]], [1]) == error


def test_analisis_existente_conserva_su_contrato():
    """Mantiene rango, nulidad y comprobación del análisis público anterior."""
    carga = json.dumps({"matriz_transformacion": [[1, 2], [2, 4]]})
    resultado = json.loads(ControladorTransformaciones.procesar(carga))
    assert resultado["estado"] == "EXITO"
    assert resultado["rango"] == 1
    assert resultado["nulidad"] == 1
    assert resultado["traza_comprobacion"]
    assert "vector_transformado" not in resultado
