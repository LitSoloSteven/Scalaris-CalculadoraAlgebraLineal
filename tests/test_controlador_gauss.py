"""Pruebas del controlador del método de Gauss para resolución de sistemas."""
from tests.comun_entradas import copiar_entrada_prueba
import json
import pytest

from src.frontend.controladores.sistemas_lineales.controlador_gauss import (
    ControladorGauss,
)
from tests.comun_controladores import procesar_sistema


def test_solucion_unica_tres_por_tres():
    """Verifica solucion unica tres por tres."""
    carga = copiar_entrada_prueba('sistema_unico')
    resultado = procesar_sistema(ControladorGauss, carga)
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion"] == ["2", "3", "-1"]
    assert len(resultado["pasos_intermedios_latex"]) > 0
    assert len(resultado["pasos_verificacion_latex"]) > 0
    for paso in resultado["pasos_verificacion_latex"]:
        assert "Incorrecto" not in paso, f"Verificación falló: {paso}"


def test_vector_b_incompleto_es_rechazado():
    """Verifica que un vector independiente incompleto retorne error explícito."""
    carga = copiar_entrada_prueba('independientes_incompletos')
    resultado = procesar_sistema(ControladorGauss, carga)
    assert resultado["estado"] == "ERROR"
    assert "1" in resultado["mensaje"] and "3" in resultado["mensaje"]


def test_matriz_irregular_es_rechazada():
    """Verifica el rechazo de matrices con filas de longitud dispar."""
    carga = copiar_entrada_prueba('filas_irregulares')
    resultado = procesar_sistema(ControladorGauss, carga)
    assert resultado["estado"] == "ERROR"
    assert "fila" in resultado["mensaje"].lower()


def test_sistema_sin_solucion():
    """Verifica el diagnóstico correcto de inconsistencia."""
    carga = copiar_entrada_prueba('sistema_inconsistente')
    resultado = procesar_sistema(ControladorGauss, carga)
    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["solucion"] is None
    assert "inconsistente" in resultado["clasificacion"].lower()


def test_celda_no_numerica_reporta_coordenadas():
    """Verifica reporte exacto de coordenadas para celdas no válidas."""
    carga = {
        "matriz_a": [["abc", "1"], ["1", "1"]],
        "vector_b": ["1", "1"],
        "variables": ["x1", "x2"],
    }
    resultado = procesar_sistema(ControladorGauss, carga)
    assert resultado["estado"] == "ERROR"
    assert "A[1,1]" in resultado["mensaje"]


def test_carga_json_malformado():
    """Verifica manejo seguro ante cadenas JSON con sintaxis rota."""
    resultado = json.loads(ControladorGauss.procesar_sistema("esto no es json {{{"))
    assert resultado["estado"] == "ERROR"
    assert "JSON" in resultado["mensaje"] or "json" in resultado["mensaje"]


def test_verificacion_con_solucion_fraccionaria():
    """Verifica que la comprobación mantenga fracciones analíticas exactas."""
    carga = copiar_entrada_prueba('sistema_fraccionario')
    resultado = procesar_sistema(ControladorGauss, carga)

    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion"] == ["9/7", "-15/14", "2/7"]

    unido = " ".join(resultado["pasos_verificacion_latex"])
    assert r"\frac{9}{7}" in unido
    assert r"\frac{15}{14}" in unido
    assert r"\frac{2}{7}" in unido
    assert "1.2857" not in unido
    assert "1.0714" not in unido
    assert "0.2857" not in unido


def test_verificacion_ausente_sin_solucion():
    """Verifica que no se generen pasos de comprobación si el sistema no tiene solución."""
    carga = {
        "matriz_a": [["1", "1"], ["1", "1"]],
        "vector_b": ["1", "2"],
        "variables": None,
    }
    resultado = procesar_sistema(ControladorGauss, carga)

    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["pasos_verificacion_latex"] == []
