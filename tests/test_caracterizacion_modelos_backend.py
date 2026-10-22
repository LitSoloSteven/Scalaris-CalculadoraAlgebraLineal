"""Conservacion exacta, contratos serializables y limites de modelos matriciales."""
from fractions import Fraction
import json
from unittest.mock import Mock

import pytest

from src.backend.constantes import DIMENSION_MAXIMA_MODELOS
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.leontief import ResolutorModeloLeontief
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.frontend.controladores.operaciones_matrices.controlador_leontief import ControladorLeontief
from src.frontend.controladores.operaciones_matrices.controlador_transformaciones import ControladorTransformaciones
from tests.comun_entradas import copiar_entrada_prueba


def test_produccion_leontief_satisface_balance_por_sector():
    """La produccion exacta cubre consumo intermedio y demanda sin alterar la entrada."""
    datos = copiar_entrada_prueba("consumo_leontief")
    demanda = copiar_entrada_prueba("demanda_leontief")
    matriz = Matriz(2, 2, datos)
    original = tuple(tuple(fila) for fila in matriz.datos)
    resultado = ResolutorModeloLeontief().resolver(matriz, demanda, ["Agricultura", "Industria"])
    produccion = [Fraction(valor) for valor in resultado["vector_produccion"]]
    assert resultado["estado"] == "EXITO"
    for indice, fila in enumerate(datos):
        consumo = sum(coeficiente * total for coeficiente, total in zip(fila, produccion))
        assert produccion[indice] - consumo == demanda[indice]
        assert Fraction(resultado["analisis_sectorial"][indice]["consumo_intermedio"]) == consumo
    assert tuple(tuple(fila) for fila in matriz.datos) == original


def test_leontief_serializa_demanda_fraccionaria_y_nombres_literales():
    """El controlador conserva nombres de usuario y racionales sin aproximar ni interpretar."""
    nombres = ["Sector <uno>", "Industria & servicios"]
    carga = {"matriz_coeficientes": [["0", "0"], ["0", "0"]],
             "vector_demanda": ["1/1001", "2/1003"], "nombres_sectores": nombres}
    resultado = json.loads(ControladorLeontief.procesar(json.dumps(carga)))
    assert resultado["estado"] == "EXITO"
    assert resultado["nombres_sectores"] == nombres
    assert resultado["vector_produccion"] == carga["vector_demanda"]
    assert resultado["vector_demanda"] == carga["vector_demanda"]


def test_imagen_usa_columnas_originales_aunque_se_intercambien_filas():
    """La base de la imagen conserva vectores originales y no columnas de la reducida."""
    datos = [[0, 2, 4], [3, 0, 3]]
    resultado = ResolutorTransformacionesLineales().resolver(Matriz(2, 3, datos))
    assert resultado["columnas_pivote"] == [0, 1]
    assert resultado["base_imagen"] == [
        {"indice_columna": 1, "vector": ["0", "3"]},
        {"indice_columna": 2, "vector": ["2", "0"]},
    ]


def test_leontief_regular_pequeno_conserva_produccion_unica():
    """Un multiplicador grande sigue siendo valido cuando el determinante es no nulo."""
    coeficiente = 1 - Fraction(1, 10**12)
    resultado = ResolutorModeloLeontief().resolver(Matriz(1, 1, [[coeficiente]]), [Fraction(1)])
    assert resultado["estado"] == "EXITO"
    assert resultado["vector_produccion"] == [str(10**12)]


def test_transformacion_racional_pequena_es_biyectiva():
    """Una matriz escalar no nula conserva rango completo y nucleo trivial."""
    resultado = ResolutorTransformacionesLineales().resolver(Matriz(1, 1, [[Fraction(1, 10**12)]]))
    assert resultado["rango"] == 1
    assert resultado["nulidad"] == 0
    assert resultado["base_nucleo"] == []
    assert resultado["es_inyectiva"] is True
    assert resultado["es_sobreyectiva"] is True


@pytest.mark.parametrize("demanda,estado", [
    (["0", "0"], "SOLUCIONES_INFINITAS"), (["1", "0"], "SIN_SOLUCION"),
])
def test_leontief_distingue_consistencia_sin_multiplicador(demanda, estado):
    """La demanda decide entre infinitas producciones e incompatibilidad cuando C es identidad."""
    carga = {"matriz_coeficientes": [["1", "0"], ["0", "1"]], "vector_demanda": demanda}
    resultado = json.loads(ControladorLeontief.procesar(json.dumps(carga)))
    assert resultado["estado"] == estado


def _carga_modelo(identificador, dimensiones):
    filas, columnas = dimensiones
    coeficientes = [["0"] * columnas for _ in range(filas)]
    if identificador == "leontief":
        return {"matriz_coeficientes": coeficientes, "vector_demanda": ["1"] * filas}
    return {"matriz_transformacion": coeficientes}


@pytest.mark.parametrize("identificador,controlador", [
    ("leontief", ControladorLeontief), ("transformaciones", ControladorTransformaciones),
])
def test_modelos_aceptan_dimension_maxima_vigente(identificador, controlador):
    """Ambos consumidores aceptan la dimension maxima del dominio con una captura valida."""
    dimensiones = (DIMENSION_MAXIMA_MODELOS, DIMENSION_MAXIMA_MODELOS)
    carga = _carga_modelo(identificador, dimensiones)
    resultado = json.loads(controlador.procesar(json.dumps(carga)))
    assert resultado["estado"] == "EXITO"


@pytest.mark.parametrize("identificador,controlador,resolutor,dimensiones", [
    ("leontief", ControladorLeontief, ResolutorModeloLeontief,
     (DIMENSION_MAXIMA_MODELOS + 1, DIMENSION_MAXIMA_MODELOS + 1)),
    ("transformaciones", ControladorTransformaciones, ResolutorTransformacionesLineales,
     (DIMENSION_MAXIMA_MODELOS + 1, DIMENSION_MAXIMA_MODELOS + 1)),
    ("transformaciones", ControladorTransformaciones, ResolutorTransformacionesLineales,
     (DIMENSION_MAXIMA_MODELOS + 1, 1)),
    ("transformaciones", ControladorTransformaciones, ResolutorTransformacionesLineales,
     (1, DIMENSION_MAXIMA_MODELOS + 1)),
])
def test_modelos_rechazan_dimension_superior_al_limite(identificador, controlador, resolutor, dimensiones, monkeypatch):
    """La captura rechaza exceso de filas o columnas antes de invocar el calculo."""
    calculo = Mock(return_value={"estado": "EXITO"})
    monkeypatch.setattr(resolutor, "resolver", calculo)
    carga = _carga_modelo(identificador, dimensiones)
    resultado = json.loads(controlador.procesar(json.dumps(carga)))
    assert resultado["estado"] == "ERROR"
    calculo.assert_not_called()
