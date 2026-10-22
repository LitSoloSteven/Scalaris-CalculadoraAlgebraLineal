"""Pruebas unitarias para el controlador de operaciones de inversión matricial."""
import json
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)


def test_controlador_inversa_dos_por_dos_exitoso():
    """Valida el cálculo de inversa 2x2, determinante y generación de pasos."""
    carga = json.dumps({
        "dimension": 2,
        "datos": [["1", "2"], ["3", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert res["estado"] == "EXITO"
    assert res["determinante_texto"] == "-2"
    assert res["matriz_a"] is not None
    assert res["matriz_a_latex"] is not None
    assert res["inversa"] is not None
    assert res["inversa_latex"] is not None
    assert len(res["comprobaciones"]) == 3
    assert all(v["coincide"] is True for v in res["comprobaciones"])

    pasos = res["pasos"]
    grupos = res["grupos"]
    estadisticas = res["estadisticas"]

    assert len(pasos) > 0
    tipos = {s["tipo"] for s in pasos}
    assert "inicial" in tipos
    assert "pivote" in tipos
    assert "eliminacion" in tipos
    assert "normalizacion" in tipos
    assert "otro" not in tipos

    for s in pasos:
        indice_grupo = s["indice_grupo"]
        assert 0 <= indice_grupo < len(grupos)
        assert s["indice"] in grupos[indice_grupo]["indices_pasos"]

    assert estadisticas["total"] == len(pasos)
    assert estadisticas["pivotes"] > 0
    assert estadisticas["eliminaciones"] > 0
    assert estadisticas["normalizaciones"] > 0


def test_controlador_inversa_celda_invalida_reporta_coordenadas():
    """Verifica que se identifique con precisión la coordenada de celda inválida."""
    carga = json.dumps({
        "dimension": 2,
        "datos": [["1", "2"], ["abc", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert res["estado"] == "ERROR"
    assert res["celda_error"] == [1, 0]
    assert "Error en A[2,1]" in res["mensaje"]


def test_controlador_inversa_limite_dimension():
    """Rechaza dimensiones que exceden el tamaño máximo permitido."""
    carga_dimension_51 = json.dumps({
        "dimension": 51,
        "datos": [["0"] * 51] * 51,
    })
    resultado_dimension_51 = ControladorOperacionesInversas.procesar_inversa(carga_dimension_51)
    assert resultado_dimension_51["estado"] == "ERROR"
    assert "entre 1 y 50" in resultado_dimension_51["mensaje"]


def test_controlador_inversa_json_malformado():
    """Rechaza cadenas que no cumplen formato JSON o no son diccionarios."""
    resultado_malformado = ControladorOperacionesInversas.procesar_inversa("not json")
    assert resultado_malformado["estado"] == "ERROR"

    resultado_no_diccionario = ControladorOperacionesInversas.procesar_inversa("[1, 2, 3]")
    assert resultado_no_diccionario["estado"] == "ERROR"


def test_controlador_inversa_matriz_singular():
    """Identifica matrices cuadradas con determinante cero como singulares."""
    carga = json.dumps({
        "dimension": 2,
        "datos": [["1", "2"], ["2", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert res["estado"] == "SINGULAR"
    assert res["determinante"] == 0
    assert res["inversa"] is None
