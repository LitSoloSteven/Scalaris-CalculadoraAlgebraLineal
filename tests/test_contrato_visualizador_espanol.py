"""Contratos únicos de captura, resultados, cuadros y transferencia geométrica."""
import ast
import json

import pytest

from src.frontend.controladores.geometria import ControladorGeometria
from src.frontend.componentes.transferencia import guardar_vectores, consumir_vectores
from tests.comun import RAIZ, limpiar_almacen_transferencia


def _vector(datos):
    return {"datos": datos, "orientacion": "columna"}


def test_resultado_vectorial_tiene_un_solo_esquema():
    """El resultado y sus 25 cuadros contienen exclusivamente campos canónicos."""
    resultado = ControladorGeometria.procesar_vectores(json.dumps({"vectores": [_vector([1, 2]), _vector([3, 4])]}))
    assert set(resultado) == {
        "estado", "numero_variables", "vector_u", "vector_v", "estatica", "cuadros",
        "cuadro_predeterminado", "rango", "fuera_de_rango", "celda_error", "mensaje",
    }
    assert set(resultado["vector_u"]) == {"aproximado", "exacta"}
    assert set(resultado["vector_v"]) == {"aproximado", "exacta"}
    assert set(resultado["estatica"]) == {"vector_u", "vector_v", "u_mas_v"}
    assert len(resultado["cuadros"]) == 25
    assert all(set(cuadro) == {"escalar", "escalar_exacto", "escalar_por_u", "escalar_por_u_mas_v"} for cuadro in resultado["cuadros"])
    assert resultado["cuadros"][resultado["cuadro_predeterminado"]]["escalar_exacto"] == "1"


def test_sistema_y_ecuaciones_tienen_un_solo_esquema():
    """Las ecuaciones y la solución puntual tienen campos descriptivos españoles."""
    resultado = ControladorGeometria.procesar_rectas_planos(json.dumps({"matriz_a": [[1, 0], [0, 1]], "vector_b": [2, 3]}))
    assert set(resultado) == {
        "estado", "numero_variables", "numero_ecuaciones", "ecuaciones", "estado_solucion",
        "conjunto_solucion", "parametro_pendiente", "banderas", "rango", "fuera_de_rango", "celda_error", "mensaje",
    }
    assert all(set(ecuacion) == {"indice", "tipo", "coeficientes", "coeficientes_exactos", "objetivo", "objetivo_exacto", "latex"} for ecuacion in resultado["ecuaciones"])
    assert set(resultado["conjunto_solucion"]) == {"tipo", "etiqueta_tipo", "dimension", "espacio_completo", "punto", "punto_exacto", "punto_latex"}
    assert resultado["conjunto_solucion"]["punto_exacto"] == ["2", "3"]


def test_combinacion_y_cadena_tienen_un_solo_esquema():
    """La cadena y los generadores conservan coordenadas y etiquetas canónicas."""
    resultado = ControladorGeometria.procesar_combinacion(json.dumps({
        "objetivo": _vector([2, 3]), "vectores": [_vector([1, 0]), _vector([0, 1])],
    }))
    assert set(resultado) == {
        "estado", "numero_variables", "objetivo", "vectores", "cadena", "representacion",
        "objetivo_fuera_del_espacio_generado", "estado_solucion", "rango", "fuera_de_rango", "celda_error", "mensaje",
    }
    assert all(set(vector) == {"aproximado", "exacta"} for vector in resultado["vectores"] + [resultado["objetivo"]])
    assert all(set(paso) == {"aproximado", "exacta", "etiqueta"} for paso in resultado["cadena"])
    assert resultado["cadena"][-1]["exacta"] == ["2", "3"]


@pytest.mark.parametrize("metodo,carga", [
    ("procesar_vectores", {"vectors": [_vector([1, 2]), _vector([3, 4])]}),
    ("procesar_vectores", {"vectores": [_vector([1, 2]), _vector([3, 4])], "vectors": []}),
    ("procesar_combinacion", {"b": _vector([1, 2]), "vectors": [_vector([1, 2])]}),
    ("procesar_combinacion", {"objetivo": _vector([1, 2]), "vectores": [_vector([1, 2])], "b": _vector([1, 2])}),
])
def test_cargas_anteriores_y_mezcladas_no_se_aceptan(metodo, carga):
    """Ni el vocabulario retirado ni una carga dual constituyen una entrada válida."""
    resultado = getattr(ControladorGeometria, metodo)(json.dumps(carga))
    assert resultado["estado"] == "ERROR"
    assert set(resultado) == {"estado", "mensaje", "celda_error"}


@pytest.mark.parametrize("entrada", [1, None, "abc", {"datos": 3}])
def test_vector_malformado_devuelve_error_sin_excepcion(entrada):
    """Un contenedor no vectorial se rechaza sin escapar del contrato de error."""
    resultado = ControladorGeometria.procesar_vectores(json.dumps({"vectores": [entrada, _vector([1, 2])]}))
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"] == "Datos de vector inválidos."


def test_transferencia_vectorial_tiene_campos_geometricos_canonicos():
    """El contenido de la transferencia usa escena y vectores sin claves alternativas."""
    limpiar_almacen_transferencia()
    token = guardar_vectores("vectores", "vectores", [["1/3", "2"], ["4", "5"]])
    resultado = consumir_vectores(token, dimensiones_permitidas={2, 3})
    assert resultado.datos == {"escena": "vectores", "vectores": [["1/3", "2"], ["4", "5"]]}


@pytest.mark.parametrize("archivo", ["controlador_rectas_planos.py", "controlador_vectores.py", "controlador_combinacion.py"])
def test_controladores_no_contienen_calculo_de_dominio(archivo):
    """Los adaptadores no importan modelos ni operaciones aritméticas de dominio."""
    ruta = RAIZ / "src/frontend/controladores/geometria" / archivo
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    assert not any(isinstance(nodo, (ast.BinOp, ast.AugAssign, ast.For)) for nodo in ast.walk(arbol))
    importaciones = [nodo.module for nodo in ast.walk(arbol) if isinstance(nodo, ast.ImportFrom)]
    assert not any("modelos" in modulo or "resolutores" in modulo or "fractions" in modulo for modulo in importaciones)
