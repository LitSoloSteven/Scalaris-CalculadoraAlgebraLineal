"""Familias nulas y relaciones de dependencia comprobadas con racionales exactos."""
import json
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.homogeneos import resolver_homogeneo
from src.backend.resolutores.operaciones_vectores.independencia import analizar_independencia
from src.frontend.controladores.operaciones_vectores.controlador_independencia import procesar_independencia
from src.frontend.controladores.sistemas_lineales import ControladorGauss, ControladorGaussJordan


@pytest.mark.parametrize("datos,rango", [
    ([[1, 0], [0, 1]], 2), ([[1, 2], [2, 4]], 1),
    ([[0, 0, 0], [0, 0, 0]], 0), ([[1, 2, 3]], 1),
    ([[1], [2], [3]], 1), ([["1/2", "1/3"], ["3/4", "1/2"]], 1),
])
def test_homogeneos_describen_y_verifican_todas_las_direcciones(datos, rango):
    """El numero de parametros es n-r y cada direccion anula exactamente A."""
    matriz = Matriz(len(datos), len(datos[0]), datos)
    resultado = resolver_homogeneo(matriz)
    assert resultado["rango"] == rango
    assert resultado["nulidad"] == matriz.columnas - rango
    assert resultado["solo_trivial"] is (rango == matriz.columnas)
    assert len(resultado["comprobaciones"]) == resultado["nulidad"] + 1
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
    for vector in resultado["direcciones"]:
        assert any(vector)
        assert all(sum(valor * componente for valor, componente in zip(fila, vector)) == 0 for fila in matriz.datos)
        assert all(isinstance(valor, Fraction) for valor in vector)
    assert resultado["formula_familia"]
    for nombre in resultado["parametros_solucion"]["nombres_parametros"]:
        assert nombre in resultado["formula_familia"]


@pytest.mark.parametrize("vectores,independiente", [
    ([[1, 0], [0, 1]], True), ([[1, 2], [2, 4]], False),
    ([[0, 0]], False), ([[1, 0], [0, 1], [1, 1]], False),
    ([["1/2", "1/3"], ["3/4", "1/2"]], False),
])
def test_independencia_muestra_relaciones_no_triviales_con_sustitucion(vectores, independiente):
    """Las relaciones propuestas son no triviales y su combinacion de columnas es cero."""
    columnas = [Matriz(len(vector), 1, [[valor] for valor in vector]) for vector in vectores]
    resultado = analizar_independencia(columnas)
    assert resultado["es_independiente"] is independiente
    assert bool(resultado["relaciones"]) is (not independiente)
    for relacion in resultado["relaciones"]:
        coeficientes = relacion["coeficientes"]
        assert any(coeficientes)
        assert all(sum(coeficiente * columna.obtener(fila, 0) for coeficiente, columna in zip(coeficientes, columnas)) == 0
                   for fila in range(columnas[0].filas))
    assert all(comprobacion["coincide"] for comprobacion in resultado["comprobaciones"])
    assert resultado["traza"][0]["detalle_latex"] == r"[v_1|\cdots|v_k]c=0"


@pytest.mark.parametrize("controlador", [ControladorGauss, ControladorGaussJordan])
def test_controlador_homogeneo_enriquece_sin_alterar_contrato_general(controlador):
    """El modo orientado agrega analisis; el flujo general conserva su respuesta previa."""
    carga = {"matriz_a": [[1, 2], [2, 4]], "vector_b": [0, 0]}
    general = json.loads(controlador.procesar_sistema(json.dumps(carga)))
    orientado = json.loads(controlador.procesar_sistema(json.dumps({**carga, "homogeneo": True})))
    assert {clave: valor for clave, valor in orientado.items() if clave != "homogeneo"} == general
    assert orientado["homogeneo"]["nulidad"] == 1
    assert orientado["homogeneo"]["comprobaciones"][1]["coincide"]
    rechazo = json.loads(controlador.procesar_sistema(json.dumps({**carga, "vector_b": [1, 0], "homogeneo": True})))
    assert rechazo["estado"] == "ERROR"


@pytest.mark.parametrize("vectores", [
    {}, {"v_1": {"datos": [1, 2], "orientacion": "fila"}},
    {"v_1": {"datos": [1, 2]}, "v_2": {"datos": [1]}},
    {"v_1": {"datos": ["1/0"]}}, {"v_1": {"datos": [1] * 11}},
])
def test_independencia_rechaza_errores_de_forma_orientacion_y_celdas(vectores):
    """No hay calculo parcial ni coeficientes ficticios para capturas invalidas."""
    resultado = json.loads(procesar_independencia(vectores))
    assert resultado["estado"] == "ERROR"
    assert "relaciones" not in resultado
