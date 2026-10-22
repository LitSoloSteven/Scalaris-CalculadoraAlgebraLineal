"""Pruebas del reproductor de pasos y agrupación didáctica para Operaciones con Vectores."""

import ast
import json
import re
from pathlib import Path
from fractions import Fraction
import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores
from src.frontend.controladores.operaciones_vectores import (
    ControladorOperacionesVectores,
)
from src.frontend.vistas.operaciones_vectores._pasos_reproductor import (
    construir_pasos_combinacion_lineal,
    construir_pasos_vector_basico,
)


def test_operaciones_basicas_generan_secuencia_de_pasos_esperada():
    """Suma, resta y multiplicación escalar generan secuencia [inicial, componentes..., resultado]."""
    v1 = Matriz(3, 1, [[1], [2], [3]])
    v2 = Matriz(3, 1, [[4], [5], [6]])

    # 1. Suma
    resultado_suma = ResolutorOperacionesVectores().sumar(v1, v2)
    pasos_suma, grupos_suma = construir_pasos_vector_basico(resultado_suma)
    tipos_suma = [p.tipo for p in pasos_suma]
    assert tipos_suma == ["inicial", "componente", "componente", "componente", "resultado"]
    assert [p.etiqueta_tipo for p in pasos_suma] == ["Inicial", "Componente", "Componente", "Componente", "Resultado"]
    assert len(grupos_suma) == 1
    assert pasos_suma[-1].meta_explicar["tipo"] == "resultado"

    # 2. Resta
    resultado_resta = ResolutorOperacionesVectores().restar(v1, v2)
    pasos_resta, grupos_resta = construir_pasos_vector_basico(resultado_resta)
    tipos_resta = [p.tipo for p in pasos_resta]
    assert tipos_resta == ["inicial", "componente", "componente", "componente", "resultado"]

    # 3. Escalar
    resultado_escalar = ResolutorOperacionesVectores().multiplicar_escalar(2, v1)
    pasos_escalar, grupos_escalar = construir_pasos_vector_basico(resultado_escalar)
    tipos_escalar = [p.tipo for p in pasos_escalar]
    assert tipos_escalar == ["inicial", "componente", "componente", "componente", "resultado"]


def test_suma_fila_columna_incluye_paso_de_ajuste():
    """La suma fila + columna incluye explícitamente el paso de ajuste de orientación."""
    vector_columna = Matriz(2, 1, [[3], [1]])
    vector_fila = Matriz(1, 2, [[2, 4]])

    res = ResolutorOperacionesVectores().sumar(vector_columna, vector_fila, estricto=False)
    pasos, grupos = construir_pasos_vector_basico(res)
    tipos = [p.tipo for p in pasos]

    assert tipos == ["inicial", "ajuste", "componente", "componente", "resultado"]
    assert pasos[1].tipo == "ajuste"
    assert pasos[1].etiqueta_tipo == "Ajuste"
    assert "orientación" in pasos[1].descripcion.lower()


def test_combinacion_lineal_agrupa_por_tipo_de_solucion():
    """La agrupación incorpora únicamente las etapas aplicables a la solución."""
    _comprobar_grupos_combinacion_unica()
    _comprobar_grupos_combinacion_infinita()
    _comprobar_grupos_combinacion_incompatible()


def _comprobar_grupos_combinacion_unica():
    carga_unica = json.dumps({
        "objetivo": {"orientacion": "columna", "datos": ["3", "2"]},
        "vectores": [
            {"orientacion": "columna", "datos": ["1", "0"]},
            {"orientacion": "columna", "datos": ["0", "1"]},
        ]
    })
    res_u = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga_unica))
    assert res_u["estado"] == "UNICA"
    pasos_u, grupos_u = construir_pasos_combinacion_lineal(res_u)
    assert len(grupos_u) == 4
    titulos_u = [g.titulo for g in grupos_u]
    assert titulos_u == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
        "Sustitución hacia atrás",
        "Comprobación",
    ]
    assert [g.tipo for g in grupos_u] == ["planteamiento", "eliminacion", "sustitucion", "verificacion"]



def _comprobar_grupos_combinacion_infinita():
    carga_infinita = json.dumps({
        "objetivo": {"orientacion": "columna", "datos": ["3", "6"]},
        "vectores": [
            {"orientacion": "columna", "datos": ["1", "2"]},
            {"orientacion": "columna", "datos": ["2", "4"]},
        ]
    })
    res_i = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga_infinita))
    assert res_i["estado"] == "INFINITA"
    pasos_i, grupos_i = construir_pasos_combinacion_lineal(res_i)
    assert len(grupos_i) == 4
    assert [g.titulo for g in grupos_i] == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
        "Sustitución hacia atrás",
        "Comprobación",
    ]
    assert any(g.tipo == "verificacion" for g in grupos_i)
    assert res_i.get("paso_verificacion") is None



def _comprobar_grupos_combinacion_incompatible():
    carga_sin_solucion = json.dumps({
        "objetivo": {"orientacion": "columna", "datos": ["0", "1"]},
        "vectores": [
            {"orientacion": "columna", "datos": ["1", "0"]},
            {"orientacion": "columna", "datos": ["2", "0"]},
        ]
    })
    res_n = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga_sin_solucion))
    assert res_n["estado"] == "SIN_SOLUCION"
    pasos_n, grupos_n = construir_pasos_combinacion_lineal(res_n)
    assert len(grupos_n) == 2
    assert [g.titulo for g in grupos_n] == [
        "Planteamiento algebraico",
        "Eliminación gaussiana",
    ]
    assert not any(g.tipo in ("sustitucion", "verificacion") for g in grupos_n)


def test_pasos_serializados_reconstruyen_matriz():
    """Cada paso de vista_pasos serializa y reconstruye su matriz usando Matriz."""
    carga = json.dumps({
        "objetivo": {"orientacion": "columna", "datos": ["7", "4", "-3"]},
        "vectores": [
            {"orientacion": "columna", "datos": ["1", "-2", "-5"]},
            {"orientacion": "columna", "datos": ["2", "5", "6"]},
        ]
    })
    res = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga))
    vista_pasos = res.get("vista_pasos", [])
    assert len(vista_pasos) > 0

    for s in vista_pasos:
        diccionario_matriz = s["matriz"]
        assert isinstance(diccionario_matriz, dict)
        assert "filas" in diccionario_matriz and "columnas" in diccionario_matriz and "datos" in diccionario_matriz
        reconstruida = Matriz(diccionario_matriz["filas"], diccionario_matriz["columnas"], diccionario_matriz["datos"])
        assert reconstruida.filas == diccionario_matriz["filas"]
        assert reconstruida.columnas == diccionario_matriz["columnas"]


def test_dimension_diez_con_nueve_vectores_genera_pasos():
    """Dimensión 10 con 9 vectores ejecuta sin error y genera pasos de reproductor."""
    datos_vectores = [
        {"orientacion": "columna", "datos": [("1" if r == c else "0") for r in range(10)]}
        for c in range(9)
    ]
    datos_objetivo = {"orientacion": "columna", "datos": [str(r + 1) for r in range(10)]}
    carga = json.dumps({"objetivo": datos_objetivo, "vectores": datos_vectores})

    res_str = ControladorOperacionesVectores.procesar_combinacion_lineal(carga)
    res = json.loads(res_str)

    assert res["estado"] in ("UNICA", "INFINITA", "SIN_SOLUCION")
    assert res["numero_variables"] == 9
    assert len(res["variables"]) == 9
    pasos, grupos = construir_pasos_combinacion_lineal(res)
    assert len(pasos) > 0
    assert len(grupos) >= 2


def test_controlador_conserva_claves_contratadas():
    """La salida conserva las claves del contrato del controlador."""
    carga = json.dumps({
        "objetivo": {"orientacion": "columna", "datos": ["1", "1"]},
        "vectores": [
            {"orientacion": "columna", "datos": ["1", "0"]},
            {"orientacion": "columna", "datos": ["0", "1"]},
        ]
    })
    res = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(carga))

    claves_requeridas = [
        "estado", "es_combinacion_lineal", "coeficientes_texto",
        "pasos_planteamiento", "pasos_gauss", "pasos", "metadatos_pasos",
        "pasos_sustitucion_regresiva", "paso_verificacion",
        "variables", "numero_variables", "vista_pasos", "grupos", "estadisticas"
    ]
    for clave in claves_requeridas:
        assert clave in res, f"Clave esperada faltante: {clave}"

    assert len(res["pasos_planteamiento"]) == 5
    assert res["paso_verificacion"] is not None
    assert "formula_latex" in res["paso_verificacion"]


def test_textos_vectoriales_sin_raya_larga_ni_voseo():
    """Los módulos vectoriales mantienen textos directos en español."""
    archivos_a_comprobar = [
        Path("src/frontend/vistas/operaciones_vectores/_pasos_reproductor.py"),
        Path("src/frontend/vistas/operaciones_vectores/mixin_pasos.py"),
        Path("src/frontend/vistas/operaciones_vectores/mixin_resultados.py"),
        Path("src/frontend/controladores/operaciones_vectores/controlador_operaciones_vectores.py"),
    ]

    patron_voseo = re.compile(
        r"\b(ingresá|añadí|escribí|presioná|pegá|sumá|calculá|mostrá|revisá)\b",
        re.IGNORECASE,
    )

    for p in archivos_a_comprobar:
        assert p.exists()
        texto = p.read_text(encoding="utf-8")
        assert "—" not in texto, f"Em-dash encontrado en {p}"
        assert "Oops" not in texto, f"Oops encontrado en {p}"

        arbol = ast.parse(texto, filename=str(p))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
                s = nodo.value
                coincidencia = patron_voseo.search(s)
                assert coincidencia is None, f"Voseo '{coincidencia.group(0)}' en {p}: {s}"
