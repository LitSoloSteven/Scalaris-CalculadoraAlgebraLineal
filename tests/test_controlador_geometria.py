"""Pruebas del controlador y algoritmos de geometría analítica."""
import copy
import json
from tests.comun_geometria import comprobar_rectas_incompatibles
from tests.comun_entradas import copiar_entrada_prueba
from fractions import Fraction
import pytest

from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
    selector_celda_error,
)


def test_selector_celda_error_matriz_a():
    """Verifica selector celda error matriz a."""
    resultado = selector_celda_error({"tipo": "A", "fila": 1, "columna": 2}, escena="rectas-planos", n_cuadricula=2)
    assert resultado == 'input[data-ecuaciones-fila="1"][data-ecuaciones-columna="2"]'


def test_selector_celda_error_vector_b():
    """Verifica selector celda error vector b."""
    resultado = selector_celda_error({"tipo": "b", "fila": 1}, escena="rectas-planos", n_cuadricula=2)
    assert resultado == 'input[data-ecuaciones-fila="1"][data-ecuaciones-columna="2"]'


def test_selector_celda_error_vector():
    """Verifica selector celda error vector."""
    resultado = selector_celda_error({"tipo": "vector", "nombre": "v_1", "indice": 0}, escena="vectores", n_cuadricula=2)
    assert resultado == 'input[data-geometria-vector="geometria_vectores_v_1"][data-geometria-indice="0"]'


def test_selector_celda_error_combinacion():
    """Verifica selector celda error combinacion."""
    resultado = selector_celda_error({"tipo": "vector", "nombre": "b", "indice": 1}, escena="combinacion", n_cuadricula=2)
    assert resultado == 'input[data-geometria-vector="geometria_combinacion_b"][data-geometria-indice="1"]'


def test_rectas_planos_carga_malformado():
    """Verifica rectas planos carga malformado."""
    resultado = ControladorGeometria.procesar_rectas_planos("not json")
    assert resultado["estado"] == "ERROR"


def test_rectas_planos_interseccion_unica_dos_por_dos():
    """Verifica rectas planos interseccion unica dos por dos."""
    carga = json.dumps({
        "matriz_a": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 2
    assert resultado["estado_solucion"] == "SOLUCION_UNICA"
    assert resultado["conjunto_solucion"]["tipo"] == "PUNTO"
    assert resultado["conjunto_solucion"]["punto"] == [2.0, 1.0]
    assert resultado["conjunto_solucion"]["punto_exacto"] == ["2", "1"]
    assert not resultado["parametro_pendiente"]
    json.dumps(resultado)


def test_rectas_planos_indicador_paralelismo():
    """Verifica rectas planos indicador paralelismo."""
    carga = json.dumps(copiar_entrada_prueba('rectas_incompatibles'))
    resultado = comprobar_rectas_incompatibles(carga)
    assert "paralelas" in resultado["banderas"]


def test_rectas_planos_degenerada_cero_igual_cero():
    """Verifica rectas planos degenerada cero igual cero."""
    carga = json.dumps({
        "matriz_a": [["0", "0"], ["1", "1"]],
        "vector_b": ["0", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    ecuaciones = resultado["ecuaciones"]
    assert ecuaciones[0]["tipo"] == "trivial"


def test_rectas_planos_degenerada_cero_igual_cinco():
    """Verifica rectas planos degenerada cero igual cinco."""
    carga = json.dumps({
        "matriz_a": [["0", "0"], ["1", "1"]],
        "vector_b": ["5", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    ecuaciones = resultado["ecuaciones"]
    assert ecuaciones[0]["tipo"] == "contradiccion"


def test_rectas_planos_dimension_cuatro_invalida():
    """Verifica rectas planos dimension cuatro invalida."""
    carga = json.dumps({
        "matriz_a": [["1", "0", "0", "0"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado.get("codigo") == "dimension_invalida"


def test_rectas_planos_dimension_diez_invalida():
    """Verifica rectas planos dimension diez invalida."""
    fila = ["1"] * 10
    carga = json.dumps({
        "matriz_a": [fila],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado.get("codigo") == "dimension_invalida"


def test_rectas_planos_fracciones_largas():
    """Verifica rectas planos fracciones largas."""
    carga = json.dumps({
        "matriz_a": [["1001/1000", "1"], ["1", "-123456789012/987654321"]],
        "vector_b": ["3", "1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    json.dumps(resultado)


def test_rectas_planos_diez_ecuaciones():
    """Verifica rectas planos diez ecuaciones."""
    filas = [["1", str(i)] for i in range(10)]
    vector_b = [str(i) for i in range(10)]
    carga = json.dumps({"matriz_a": filas, "vector_b": vector_b})
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_ecuaciones"] == 10


def test_rectas_planos_celda_erronea():
    """Verifica rectas planos celda erronea."""
    carga = json.dumps({
        "matriz_a": [["1", "abc"], ["1", "1"]],
        "vector_b": ["1", "2"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado["celda_error"] is not None
    assert resultado["celda_error"]["tipo"] == "A"


def test_rectas_planos_serializable():
    """Verifica rectas planos serializable."""
    carga = json.dumps({
        "matriz_a": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    serializado = json.dumps(resultado)
    assert isinstance(serializado, str)


def test_rectas_planos_sin_mutacion():
    """Verifica rectas planos sin mutacion."""
    diccionario_carga = {
        "matriz_a": [["1", "1"], ["1", "-1"]],
        "vector_b": ["3", "1"],
    }
    carga_str = json.dumps(diccionario_carga)
    original = copy.deepcopy(diccionario_carga)
    ControladorGeometria.procesar_rectas_planos(carga_str)
    assert diccionario_carga == original


def test_rectas_planos_tres_por_tres_solucion_unica():
    """Verifica rectas planos tres por tres solucion unica."""
    carga = json.dumps({
        "matriz_a": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "vector_b": ["1", "2", "3"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 3
    assert resultado["estado_solucion"] == "SOLUCION_UNICA"
    assert resultado["conjunto_solucion"]["punto"] == [1.0, 2.0, 3.0]


def test_rectas_planos_soluciones_infinitas():
    """Verifica rectas planos soluciones infinitas."""
    carga = json.dumps({
        "matriz_a": [["1", "1"]],
        "vector_b": ["1"],
    })
    resultado = ControladorGeometria.procesar_rectas_planos(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["parametro_pendiente"] is False
    assert resultado["conjunto_solucion"] is not None
    assert resultado["conjunto_solucion"]["tipo"] == "RECTA"
    assert "segmento" in resultado["conjunto_solucion"] and resultado["conjunto_solucion"]["segmento"] is not None


def test_vectores_basico_dos_dimensiones():
    """Verifica vectores basico dos dimensiones."""
    carga = json.dumps({
        "vectores": [
            {"datos": ["1", "0"], "orientacion": "columna"},
            {"datos": ["0", "1"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(carga)
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_variables"] == 2
    assert len(resultado["cuadros"]) == 25


def test_vectores_cuadro_predeterminado_k_uno():
    """Verifica vectores cuadro predeterminado k uno."""
    carga = json.dumps({
        "vectores": [
            {"datos": ["2", "3"], "orientacion": "columna"},
            {"datos": ["1", "1"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(carga)
    assert resultado["estado"] == "EXITO"
    cuadro_defecto = resultado["cuadro_predeterminado"]
    cuadro = resultado["cuadros"][cuadro_defecto]
    u = resultado["vector_u"]["aproximado"]
    v = resultado["vector_v"]["aproximado"]
    assert cuadro["escalar_por_u"] == u
    assert cuadro["escalar_por_u_mas_v"] == [u[0] + v[0], u[1] + v[1]]


def test_vectores_rango_cubre_todos_los_cuadros():
    """Verifica vectores rango cubre todos los cuadros."""
    carga = json.dumps({
        "vectores": [
            {"datos": ["10", "0"], "orientacion": "columna"},
            {"datos": ["0", "1"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(carga)
    r = resultado["rango"]
    assert r[1] >= 30


def test_vectores_dimension_cuatro_invalida():
    """Verifica vectores dimension cuatro invalida."""
    carga = json.dumps({
        "vectores": [
            {"datos": ["1", "0", "0", "0"], "orientacion": "columna"},
            {"datos": ["0", "1", "0", "0"], "orientacion": "columna"},
        ],
    })
    resultado = ControladorGeometria.procesar_vectores(carga)
    assert resultado["estado"] == "ERROR"
    assert resultado.get("codigo") == "dimension_invalida"
