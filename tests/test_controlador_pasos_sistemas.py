"""Pruebas para los pasos, serialización y reproductor en sistemas de ecuaciones."""
from tests.comun_entradas import copiar_entrada_prueba
import json
from fractions import Fraction
import pytest

from src.backend.modelos.matriz import Matriz
from src.frontend.controladores.sistemas_lineales.controlador_gauss import (
    ControladorGauss,
)
from src.frontend.controladores.sistemas_lineales.controlador_gauss_jordan import (
    ControladorGaussJordan,
)
from src.frontend.vistas.sistemas_lineales._pasos_reproductor import (
    construir_pasos_reproductor,
)


def _resolver_gauss(carga: dict) -> dict:
    """Resuelve el sistema utilizando el controlador de Gauss."""
    return json.loads(ControladorGauss.procesar_sistema(json.dumps(carga)))


def _resolver_gauss_jordan(carga: dict) -> dict:
    """Resuelve el sistema utilizando el controlador de Gauss-Jordan."""
    return json.loads(ControladorGaussJordan.procesar_sistema(json.dumps(carga)))


def test_contrato_pasos_presente_en_gauss_y_gauss_jordan():
    """Verifica que tanto Gauss como Gauss-Jordan incluyan las claves requeridas."""
    carga = copiar_entrada_prueba('sistema_unico')
    for res in (_resolver_gauss(carga), _resolver_gauss_jordan(carga)):
        assert "variables" in res
        assert res["variables"] == ["x1", "x2", "x3"]
        assert "numero_variables" in res
        assert res["numero_variables"] == 3
        assert "vista_pasos" in res
        assert isinstance(res["vista_pasos"], list) and len(res["vista_pasos"]) > 0
        assert "grupos" in res
        assert isinstance(res["grupos"], list) and len(res["grupos"]) > 0
        assert "estadisticas" in res
        assert isinstance(res["estadisticas"], dict)
        for clave_estadistica in ("total", "pivotes", "intercambios", "eliminaciones", "normalizaciones"):
            assert clave_estadistica in res["estadisticas"]


def test_variables_por_defecto_si_vienen_none():
    """Si variables es None, debe generar x1..xn automáticamente."""
    carga = {
        "matriz_a": [["1", "2"], ["3", "4"]],
        "vector_b": ["5", "6"],
        "variables": None,
    }
    res_g = _resolver_gauss(carga)
    res_gj = _resolver_gauss_jordan(carga)
    assert res_g["variables"] == ["x1", "x2"]
    assert res_gj["variables"] == ["x1", "x2"]


def test_cada_paso_reconstruye_matriz_exacta():
    """Cada elemento de vista_pasos['matriz'] debe reconstruirse como Matriz exacta."""
    carga = copiar_entrada_prueba('sistema_unico')
    for res in (_resolver_gauss(carga), _resolver_gauss_jordan(carga)):
        for paso in res["vista_pasos"]:
            diccionario_matriz = paso["matriz"]
            assert "filas" in diccionario_matriz
            assert "columnas" in diccionario_matriz
            assert "datos" in diccionario_matriz
            reconstruida = Matriz(diccionario_matriz["filas"], diccionario_matriz["columnas"], diccionario_matriz["datos"])
            assert reconstruida.filas == diccionario_matriz["filas"]
            assert reconstruida.columnas == diccionario_matriz["columnas"]
            assert len(reconstruida.datos) == diccionario_matriz["filas"]


def test_tipos_de_paso_siempre_clasificados():
    """El tipo de cada paso en vista_pasos no debe ser nunca 'otro'."""
    cargas = [
        copiar_entrada_prueba('sistema_unico'),
        {
            "matriz_a": [["0", "2", "1"], ["3", "1", "-1"], ["1", "-1", "2"]],
            "vector_b": ["5", "4", "3"],
            "variables": ["x1", "x2", "x3"],
        },
        {
            "matriz_a": [["1", "1"], ["1", "1"]],
            "vector_b": ["1", "2"],
            "variables": ["x1", "x2"],
        },
        {
            "matriz_a": [["1", "2", "3"], ["2", "4", "6"], ["-1", "-2", "-3"]],
            "vector_b": ["1", "2", "-1"],
            "variables": ["x1", "x2", "x3"],
        },
    ]

    tipos_validos = {"inicial", "intercambio", "pivote", "eliminacion", "normalizacion"}

    for carga in cargas:
        for funcion_resolucion in (_resolver_gauss, _resolver_gauss_jordan):
            res = funcion_resolucion(carga)
            for paso in res["vista_pasos"]:
                tipo = paso["tipo"]
                assert tipo != "otro", f"Paso clasificado como 'otro': {paso}"
                assert tipo in tipos_validos, f"Tipo inesperado: {tipo}"


def test_sistema_3x3_con_intercambio():
    """Un sistema 3x3 que fuerza intercambio de filas debe reflejarlo en estadísticas y filas_intercambiadas."""
    carga = {
        "matriz_a": [["0", "2", "1"], ["3", "1", "-1"], ["1", "-1", "2"]],
        "vector_b": ["5", "4", "3"],
        "variables": ["x1", "x2", "x3"],
    }
    for res in (_resolver_gauss(carga), _resolver_gauss_jordan(carga)):
        assert res["estado"] == "SOLUCION_UNICA"
        assert res["estadisticas"]["intercambios"] >= 1
        pasos_intercambio = [s for s in res["vista_pasos"] if s["tipo"] == "intercambio"]
        assert len(pasos_intercambio) >= 1
        primer_intercambio = pasos_intercambio[0]
        assert primer_intercambio["filas_intercambiadas"] is not None
        assert len(primer_intercambio["filas_intercambiadas"]) == 2
        assert len(primer_intercambio["filas_cambiadas"]) == 2
        grupos_intercambio = [g for g in res["grupos"] if "intercambio" in g["titulo"]]
        assert len(grupos_intercambio) >= 1


def test_sistema_10x10_fracciones_denominador_cuatro_digitos():
    """Sistema 10x10 con denominadores de 4 dígitos debe resolverse y reconstruirse."""
    m = 10
    matriz_a = [["0"] * m for _ in range(m)]
    vector_b = [f"{i + 1}/1001" for i in range(m)]

    for i in range(m):
        matriz_a[i][i] = f"{i + 2}/1001"
        if i + 1 < m:
            matriz_a[i][i + 1] = "1/1001"
        if i > 0:
            matriz_a[i][i - 1] = "1/1001"

    carga = {
        "matriz_a": matriz_a,
        "vector_b": vector_b,
        "variables": [f"x{i+1}" for i in range(m)],
    }

    for funcion_resolucion in (_resolver_gauss, _resolver_gauss_jordan):
        res = funcion_resolucion(carga)
        assert res["estado"] == "SOLUCION_UNICA"
        assert len(res["vista_pasos"]) > 0
        for paso in res["vista_pasos"]:
            diccionario_matriz = paso["matriz"]
            reconstruida = Matriz(diccionario_matriz["filas"], diccionario_matriz["columnas"], diccionario_matriz["datos"])
            assert reconstruida.filas == m
            assert reconstruida.columnas == m + 1


def test_sistemas_incompatibles_e_indeterminados_conservan_pasos():
    """Sistemas inconsistentes e indeterminados deben incluir vista_pasos, grupos y estadísticas."""
    carga_sin_solucion = copiar_entrada_prueba('sistema_paralelo')
    for funcion_resolucion in (_resolver_gauss, _resolver_gauss_jordan):
        res = funcion_resolucion(carga_sin_solucion)
        assert res["estado"] == "SIN_SOLUCION"
        assert len(res["vista_pasos"]) > 0
        assert len(res["grupos"]) > 0
        assert res["estadisticas"]["total"] == len(res["vista_pasos"])

    carga_infinita = copiar_entrada_prueba('sistema_indeterminado')
    for funcion_resolucion in (_resolver_gauss, _resolver_gauss_jordan):
        res = funcion_resolucion(carga_infinita)
        assert res["estado"] == "SOLUCIONES_INFINITAS"
        assert len(res["vista_pasos"]) > 0
        assert len(res["grupos"]) > 0
        assert res["estadisticas"]["total"] == len(res["vista_pasos"])


def test_claves_antiguas_siguen_identicas():
    """Verifica que las claves existentes del contrato conserven valores y estructura."""
    carga = copiar_entrada_prueba('sistema_unico')

    res_g = _resolver_gauss(carga)
    assert res_g["estado"] == "SOLUCION_UNICA"
    assert res_g["solucion"] == ["2", "3", "-1"]
    assert "pasos_intermedios_latex" in res_g
    assert len(res_g["pasos_intermedios_latex"]) > 0
    assert "metadatos_pasos" in res_g
    assert len(res_g["metadatos_pasos"]) == len(res_g["pasos_intermedios_latex"])
    assert "pasos_sustitucion_regresiva" in res_g
    assert len(res_g["pasos_sustitucion_regresiva"]) > 0
    assert "pasos_verificacion_latex" in res_g
    assert len(res_g["pasos_verificacion_latex"]) > 0

    res_gj = _resolver_gauss_jordan(carga)
    assert res_gj["estado"] == "SOLUCION_UNICA"
    assert res_gj["solucion"] == ["2", "3", "-1"]
    assert "pasos_intermedios_latex" in res_gj
    assert len(res_gj["pasos_intermedios_latex"]) > 0
    assert "metadatos_pasos" in res_gj
    assert len(res_gj["metadatos_pasos"]) == len(res_gj["pasos_intermedios_latex"])
    assert "pasos_verificacion_latex" in res_gj
    assert len(res_gj["pasos_verificacion_latex"]) > 0


def test_pasos_reproductor_genera_grupos_esperados():
    """El reproductor agrupa los pasos según el tipo de solución."""
    _comprobar_grupos_solucion_unica()
    _comprobar_grupos_soluciones_no_unicas()


def _comprobar_grupos_solucion_unica():
    carga_unica = copiar_entrada_prueba('sistema_unico')
    res_u_g = _resolver_gauss(carga_unica)
    pasos_g, grupos_g = construir_pasos_reproductor(res_u_g, metodo="gauss")
    assert len(pasos_g) > 0
    assert len(grupos_g) >= 3
    titulos_g = [g.titulo for g in grupos_g]
    assert "Sustitución hacia atrás" in titulos_g
    assert "Comprobación Ax = b" in titulos_g
    tipos_pasos_g = {p.tipo for p in pasos_g}
    assert "sustitucion" in tipos_pasos_g
    assert "verificacion" in tipos_pasos_g

    res_u_gj = _resolver_gauss_jordan(carga_unica)
    pasos_gj, grupos_gj = construir_pasos_reproductor(res_u_gj, metodo="gauss-jordan")
    titulos_gj = [g.titulo for g in grupos_gj]
    assert "Solución final" in titulos_gj
    assert "Comprobación Ax = b" in titulos_gj


def _comprobar_grupos_soluciones_no_unicas():
    carga_infinita = copiar_entrada_prueba('sistema_indeterminado')
    res_inf = _resolver_gauss(carga_infinita)
    pasos_inf, grupos_inf = construir_pasos_reproductor(res_inf, metodo="gauss")
    titulos_inf = [g.titulo for g in grupos_inf]
    assert "Sustitución hacia atrás" in titulos_inf
    assert "Comprobación Ax = b" not in titulos_inf

    carga_sin_solucion = copiar_entrada_prueba('sistema_paralelo')
    res_no = _resolver_gauss(carga_sin_solucion)
    pasos_no, grupos_no = construir_pasos_reproductor(res_no, metodo="gauss")
    titulos_no = [g.titulo for g in grupos_no]
    assert "Sustitución hacia atrás" not in titulos_no
    assert "Solución final" not in titulos_no
    assert "Comprobación Ax = b" not in titulos_no
    assert all(p.tipo in ("inicial", "intercambio", "pivote", "eliminacion", "normalizacion") for p in pasos_no)
