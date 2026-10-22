"""Pruebas del controlador del método de Gauss-Jordan para resolución de sistemas."""
from tests.comun_entradas import copiar_entrada_prueba
import json
import pytest

from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import (
    ControladorGaussJordan,
)
from tests.comun_controladores import procesar_sistema


def test_solucion_unica_tres_por_tres():
    """Verifica solucion unica tres por tres."""
    carga = copiar_entrada_prueba('sistema_unico')
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion"] == ["2", "3", "-1"]
    for paso in resultado["pasos_verificacion_latex"]:
        assert "Incorrecto" not in paso


def test_vector_b_incompleto_es_rechazado():
    """Verifica vector b incompleto es rechazado."""
    carga = copiar_entrada_prueba('independientes_incompletos')
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "ERROR"
    assert "1" in resultado["mensaje"] and "3" in resultado["mensaje"]


def test_matriz_irregular_es_rechazada():
    """Verifica matriz irregular es rechazada."""
    carga = copiar_entrada_prueba('filas_irregulares')
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "ERROR"
    assert "fila" in resultado["mensaje"].lower()


def test_division_por_cero_en_celda_es_capturada():
    """Verifica que '1/0' sea detectado y no lance excepción no controlada."""
    carga = {
        "matriz_a": [["1/0", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "ERROR"
    assert "numérico" in resultado["mensaje"].lower() or "cero" in resultado["mensaje"].lower()


def test_carga_json_malformado():
    """Verifica carga json malformado."""
    resultado = json.loads(ControladorGaussJordan.procesar_sistema("no es json"))
    assert resultado["estado"] == "ERROR"
    assert "JSON" in resultado["mensaje"] or "json" in resultado["mensaje"]


def test_sistema_sin_solucion():
    """Verifica sistema sin solucion."""
    carga = copiar_entrada_prueba('sistema_inconsistente')
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "SIN_SOLUCION"


def test_verificacion_con_solucion_fraccionaria():
    """Verifica que el sistema con solución fraccionaria verifique sin error."""
    carga = {
        "matriz_a": [["1", "2", "3"], ["3", "2", "1"], ["-1", "-2", "22"]],
        "vector_b": ["0", "9", "2"],
        "variables": ["x1", "x2", "x3"],
    }
    resultado = procesar_sistema(ControladorGaussJordan, carga)
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert any("/" in s for s in resultado["solucion"]), f"Se esperaba fracción en {resultado['solucion']}"
    assert len(resultado["pasos_verificacion_latex"]) > 0
    for paso in resultado["pasos_verificacion_latex"]:
        assert "Incorrecto" not in paso, f"Verificación falló: {paso}"
