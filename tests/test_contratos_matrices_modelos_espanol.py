"""Contratos canónicos de evaluación, Leontief y transformaciones."""
import json
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import EvaluadorExpresionesMatriciales
from src.frontend.controladores.operaciones_matrices import (
    ControladorLeontief, ControladorOperacionesMatrices, ControladorTransformaciones,
)
from src.frontend.vistas.operaciones_matrices._ejemplos_leontief import EJEMPLOS_LEONTIEF
from src.frontend.vistas.operaciones_matrices._ejemplos_transformaciones import EJEMPLOS_TRANSFORMACIONES

CLAVES_SEGMENTO = {
    "variable_temporal", "representacion_operacion", "tipo_operacion",
    "nombre_operando_a", "nombre_operando_b", "matriz_simbolica_latex",
    "matriz_resultado_latex", "matriz_resultado", "pasos_celda_a_celda",
}


@pytest.mark.parametrize("expresion", ["A+A", "A*A", "-A", "A^T", "2A"])
def test_evaluador_entrega_solo_contrato_canonico(expresion):
    """Cada operación entrega las mismas claves españolas sin duplicados ni alias."""
    matriz = Matriz(1, 1, [[Fraction(1, 3)]])
    resultado = EvaluadorExpresionesMatriciales().evaluar(expresion, {"A": matriz})
    assert set(resultado) == {
        "estado", "mensaje", "variable_final", "matriz_resultado",
        "matriz_resultado_latex", "pasos_segmento",
    }
    assert resultado["estado"] == "EXITO"
    assert all(set(paso) == CLAVES_SEGMENTO for paso in resultado["pasos_segmento"])


def test_error_evaluador_sin_duplicados():
    """El error conserva el sobre y un resultado vacío único."""
    resultado = EvaluadorExpresionesMatriciales().evaluar("B", {"A": Matriz(1, 1)})
    assert resultado == {
        "estado": "ERROR", "mensaje": "La matriz 'B' no ha sido definida.",
        "matriz_resultado": None, "pasos_segmento": [],
    }


def test_nombre_literal_del_usuario_se_conserva():
    """Una matriz llamada data_1 es dato de usuario y conserva el nombre admitido."""
    carga = {"data_1": {"filas": 1, "columnas": 1, "datos": [["1/1001"]]}}
    resultado = json.loads(ControladorOperacionesMatrices.procesar_expresion("data_1", json.dumps(carga)))
    assert resultado["variable_final"] == "data_1"
    assert resultado["matriz_resultado"] == {"filas": 1, "columnas": 1, "datos": [["1/1001"]]}


def test_carga_matricial_antiguo_no_se_acepta():
    """La captura solo acepta dimensiones y datos en español."""
    carga = {"A": {"rows": 1, "cols": 1, "data": [["1"]]}}
    resultado = json.loads(ControladorOperacionesMatrices.procesar_expresion("A", json.dumps(carga)))
    assert resultado["estado"] == "ERROR"
    assert "'filas'" in resultado["mensaje"]


@pytest.mark.parametrize("ejemplo", EJEMPLOS_LEONTIEF)
def test_ejemplos_leontief_consumen_contrato_espanol(ejemplo):
    """Los ejemplos mantienen demanda, nombres y viabilidad sin claves abreviadas."""
    resultado = json.loads(ControladorLeontief.procesar(json.dumps(ejemplo)))
    assert resultado["estado"] == "EXITO"
    assert resultado["numero_sectores"] == len(ejemplo["nombres_sectores"])
    assert resultado["nombres_sectores"] == ejemplo["nombres_sectores"]
    assert resultado["vector_demanda"] == ejemplo["vector_demanda"]
    assert "viable" not in resultado["hawkins_simon"]
    assert not {"n", "sectores", "C", "d"} & resultado.keys()


@pytest.mark.parametrize("ejemplo", EJEMPLOS_TRANSFORMACIONES)
def test_ejemplos_transformaciones_consumen_contrato_espanol(ejemplo):
    """Las dimensiones de dominio y codominio conservan su orientación y rango."""
    resultado = json.loads(ControladorTransformaciones.procesar(json.dumps(ejemplo)))
    assert resultado["estado"] == "EXITO"
    assert resultado["dimension_dominio"] == len(ejemplo["matriz_transformacion"][0])
    assert resultado["dimension_codominio"] == len(ejemplo["matriz_transformacion"])
    assert resultado["rango"] + resultado["nulidad"] == resultado["dimension_dominio"]
    assert "aviso_convencion" in resultado
    assert not {"m", "n", "callout_convencion"} & resultado.keys()


@pytest.mark.parametrize("controlador,carga", [
    (ControladorLeontief, {"C": [["0"]], "d": ["1"], "sectores": ["Sector"]}),
    (ControladorTransformaciones, {"A": [["1"]], "variables": ["x"]}),
])
def test_modelos_rechazan_carga_antiguo(controlador, carga):
    """Los controladores no mantienen compatibilidad dual con cargas anteriores."""
    assert json.loads(controlador.procesar(json.dumps(carga)))["estado"] == "ERROR"


@pytest.mark.parametrize("controlador", [ControladorLeontief, ControladorTransformaciones])
@pytest.mark.parametrize("carga", [[], None, "texto", 12])
def test_modelos_rechazan_raiz_no_objeto(controlador, carga):
    """Las entradas JSON ajenas al contrato producen un error controlado."""
    resultado = json.loads(controlador.procesar(json.dumps(carga)))
    assert resultado["estado"] == "ERROR"
    assert "objeto JSON" in resultado["mensaje"]


@pytest.mark.parametrize("controlador", [ControladorLeontief, ControladorTransformaciones])
def test_modelos_conservan_mensaje_json_invalido(controlador):
    """La sintaxis JSON inválida conserva el mensaje previo, sin detalles de ejecución."""
    resultado = json.loads(controlador.procesar("{bad"))
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"].startswith("Carga JSON inválida:")


@pytest.mark.parametrize("controlador,carga,coordenada", [
    (ControladorLeontief, {"matriz_coeficientes": [["1/0"]], "vector_demanda": ["1"]}, "C[1,1]"),
    (ControladorLeontief, {"matriz_coeficientes": [["0"]], "vector_demanda": ["1/0"]}, "d[1]"),
    (ControladorTransformaciones, {"matriz_transformacion": [["1/0"]]}, "A[1,1]"),
])
def test_modelos_conservan_coordenada_del_error(controlador, carga, coordenada):
    """Los símbolos matemáticos de mensajes permanecen intactos tras migrar claves."""
    resultado = json.loads(controlador.procesar(json.dumps(carga)))
    assert resultado["estado"] == "ERROR"
    assert coordenada in resultado["mensaje"]


@pytest.mark.parametrize("valor,estado", [(None, "EXITO"), (" ", "ERROR")])
def test_modelos_conservan_politica_de_celdas_vacias(valor, estado):
    """Los modelos admiten None como cero y rechazan texto vacío según el contrato previo."""
    resultado = json.loads(ControladorTransformaciones.procesar(json.dumps({"matriz_transformacion": [[valor]]})))
    assert resultado["estado"] == estado
    if estado == "EXITO":
        assert resultado["rango"] == 0
    else:
        assert resultado["mensaje"] == "A[1,1]: El campo está vacío."
