"""Contratos únicos de transferencia, validación y conservación de datos exactos."""
from dataclasses import asdict

import pytest

from src.backend.constantes import MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
from src.backend.utilidades import transferencias
from src.frontend.componentes import transferencia


@pytest.mark.parametrize("tipo", ["matriz_a", "sistema", "vectores"])
def test_productor_y_consumidor_comparten_el_unico_sobre(tipo):
    """Los tres destinos recuperan exactamente los datos del sobre canónico."""
    datos = [["1/1001", "-2/3"], ["0", "1"]]
    if tipo == "matriz_a":
        token = transferencia.guardar_matriz("matrices", datos)
        esperado = datos
        consumir = lambda: transferencia.consumir_matriz(token, dimension_maxima=50)
    elif tipo == "sistema":
        esperado = {"matriz_a": datos, "vector_b": ["-1/7", "2"]}
        token = transferencia.guardar_sistema("sistemas", datos, esperado["vector_b"])
        consumir = lambda: transferencia.consumir_sistema(
            token, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    else:
        esperado = {"escena": "vectores", "vectores": datos}
        token = transferencia.guardar_vectores("vectores", "vectores", datos)
        consumir = lambda: transferencia.consumir_vectores(token, dimensiones_permitidas={2, 3})
    carga = transferencia._ALMACEN[token][1]
    claves = {"version", "tipo", "origen", "datos"} | ({"escena"} if tipo == "vectores" else set())
    assert set(carga) == claves
    assert carga["version"] == 1 and carga["tipo"] == tipo
    resultado = consumir()
    assert set(asdict(resultado)) == {"estado", "datos", "nombre_origen", "mensaje"}
    assert resultado.estado == "exito" and resultado.datos == esperado
    assert resultado.nombre_origen and resultado.mensaje == ""
    assert consumir().estado == "ausente"


@pytest.mark.parametrize("clave,valor", [
    ("v", 1), ("source", "matrices"), ("data", [["1"]]),
    ("kind", "matriz_a"), ("scene", "vectores"),
])
def test_sobre_rechaza_campos_alternativos_aunque_contenga_los_canonicos(clave, valor):
    """Las claves anteriores no constituyen un segundo contrato aceptado."""
    carga = {"version": 1, "tipo": "matriz_a", "origen": "matrices", "datos": [["1"]], clave: valor}
    assert transferencias.validar_carga_matriz(carga, dimension_maxima=50) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("carga", [
    None, [], "matriz", {"version": True, "tipo": "matriz_a", "origen": "matrices", "datos": [["1"]]},
    {"version": 1, "tipo": "matriz_a", "origen": [], "datos": [["1"]]},
    {"v": 1, "tipo": "matriz_a", "source": "matrices", "data": [["1"]]},
])
def test_matriz_rechaza_envolturas_malformadas(carga):
    """El dominio devuelve un error controlado para raíces y versiones inválidas."""
    assert transferencias.validar_carga_matriz(carga, dimension_maxima=50) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("tipo,datos", [
    ("sistema", {"matriz_a": [None], "vector_b": ["1"]}),
    ("sistema", {"matriz_a": ["12"], "vector_b": ["1"]}),
    ("sistema", {"matrix_A": [["1", "0"]], "vector_b": ["1"]}),
    ("sistema", {"matriz_a": [["1", "0"]], "vector_b": []}),
    ("vectores", [None]), ("vectores", ["12"]), ("vectores", [["1", "0"], None]),
])
def test_destinos_rechazan_contenedores_malformados_sin_excepciones(tipo, datos):
    """La validación antecede a cualquier lectura de dimensiones o celdas."""
    carga = {"version": 1, "tipo": tipo, "origen": "sistemas", "datos": datos}
    if tipo == "sistema":
        resultado = transferencias.validar_carga_sistema(
            carga, maximo_ecuaciones=10, dimensiones_permitidas={2, 3})
    else:
        carga["escena"] = "vectores"
        resultado = transferencias.validar_carga_vectores(carga, dimensiones_permitidas={2, 3})
    assert resultado == (None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


def test_limite_matricial_y_celdas_invalidas_conservan_errores():
    """La carga sobredimensionada y los números inválidos mantienen mensajes granulares."""
    carga = {"version": 1, "tipo": "matriz_a", "origen": "matrices", "datos": [["1", "0"], ["0", "1"]]}
    assert transferencias.validar_carga_matriz(carga, dimension_maxima=1) == (
        None, "La matriz es de 2×2 y esta herramienta admite hasta 1×1. Empezamos con la herramienta vacía.")
    carga["datos"] = [["1/0"]]
    assert transferencias.validar_carga_matriz(carga, dimension_maxima=50) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)
