"""Contratos vectoriales canónicos y caracterización de entradas desfavorables."""
import ast
import json
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.captura import construir_vector_desde_diccionario
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores
from src.frontend.controladores.operaciones_vectores.captura import capturar_vectores, preparar_transferencia
from src.frontend.controladores.operaciones_vectores.controlador_operaciones_vectores import ControladorOperacionesVectores
from src.frontend.controladores.operaciones_vectores.presentacion_pasos import construir_tabla_paso_vectorial
from src.frontend.componentes.captura_vectores import _formatear_nombre_vector
from tests.comun import RAIZ
from tests.comun_vista_vectorial import vista_vectorial_montada

CLAVES_COMBINACION = {
    "estado", "mensaje", "es_combinacion_lineal", "coeficientes", "coeficientes_texto",
    "solucion_parametrica", "parametros_libres", "pasos_planteamiento", "pasos_gauss",
    "pasos", "pasos_sustitucion_regresiva", "paso_verificacion",
}
CLAVES_VERIFICACION = {
    "descripcion", "formula_latex", "sustitucion_latex", "vector_evaluado_latex",
    "comparacion_latex", "detalle_latex", "coincide", "traza",
}


def _vector(datos, orientacion="columna"):
    return {"orientacion": orientacion, "datos": datos}


def _calcular_binaria(operacion, estricto, orientacion):
    carga = {"operacion": operacion, "estricto": estricto,
             "vector_1": _vector(["1/1001", "2"]),
             "vector_2": _vector(["2/1001", "3"], orientacion)}
    return json.loads(ControladorOperacionesVectores.procesar_suma_resta(json.dumps(carga)))


@pytest.mark.parametrize("operacion,esperado", [("suma", ["3/1001", "5"]), ("resta", ["-1/1001", "-1"])])
@pytest.mark.parametrize("estricto", [False, True])
@pytest.mark.parametrize("orientacion", ["columna", "fila"])
def test_orientaciones_y_fracciones_exactas(operacion, esperado, estricto, orientacion):
    """La mezcla estricta falla; la flexible conserva fracciones y el ajuste literal."""
    resultado = _calcular_binaria(operacion, estricto, orientacion)
    if estricto and orientacion == "fila":
        assert resultado == {"estado": "ERROR", "mensaje": "v_2: se esperaba forma 2×1 para coincidir con v_1; recibido 1×2 (estricto=True).",
                             "matriz_resultado": None, "pasos": [], "detalles_latex": []}
        return
    assert resultado["estado"] == "EXITO"
    assert resultado["matriz_resultado"] == {"filas": 2, "columnas": 1, "datos": [[valor] for valor in esperado]}
    assert set(resultado) == {"estado", "mensaje", "matriz_resultado", "matriz_resultado_latex", "vector_resultado_latex", "pasos", "detalles_latex"}
    if orientacion == "fila":
        assert resultado["pasos"][1]["descripcion"] == "Ajuste de orientación: v_2 era fila y se transpone a 2×1 para coincidir con v_1."


@pytest.mark.parametrize("orientacion", ["columna", "fila"])
def test_dimension_diez_y_denominador_de_cuatro_digitos(orientacion):
    """El producto conserva las diez componentes exactas, su forma y once pasos."""
    entrada = _vector([str(indice) for indice in range(1, 11)], orientacion)
    matriz = construir_vector_desde_diccionario(entrada)
    resultado = ResolutorOperacionesVectores().multiplicar_escalar("1/1009", matriz)
    esperado = [Fraction(indice, 1009) for indice in range(1, 11)]
    assert resultado["matriz_resultado"].datos == ([[valor] for valor in esperado] if orientacion == "columna" else [esperado])
    assert len(resultado["pasos"]) == 11
    assert resultado["detalles_latex"][-1] == resultado["vector_resultado_latex"]
    assert r"\frac{10}{1009}" in resultado["vector_resultado_latex"]


@pytest.mark.parametrize("objetivo,generadores,estado", [
    ([1, 2], [[1, 1]], "SIN_SOLUCION"),
    ([3, 6], [[1, 2], [2, 4]], "INFINITA"),
    ([1, 1], [[1001, 0], [0, 1009]], "UNICA"),
    ([1, 2], [], "ERROR"),
])
def test_combinacion_contrato_y_clasificacion(objetivo, generadores, estado):
    """Todos los estados conservan pasos canónicos; la representación única se verifica."""
    matriz_objetivo = Matriz(2, 1, [[valor] for valor in objetivo])
    matrices = [Matriz(2, 1, [[valor] for valor in vector]) for vector in generadores]
    resultado = ResolutorCombinacionLineal().resolver(matriz_objetivo, matrices)
    assert set(resultado) == CLAVES_COMBINACION | ({"traza_comprobacion"} if estado == "INFINITA" else set())
    assert resultado["estado"] == estado
    if estado == "ERROR":
        assert resultado["pasos_planteamiento"] == resultado["pasos_gauss"] == []
        return
    assert len(resultado["pasos_planteamiento"]) == 5
    assert [paso["numero_paso"] for paso in resultado["pasos"]] == list(range(1, len(resultado["pasos"]) + 1))
    assert all(set(paso) == {"numero_paso", "descripcion", "detalle_latex", "matriz"} for paso in resultado["pasos"])
    _comprobar_solucion(resultado, estado)


def _comprobar_solucion(resultado, estado):
    if estado == "UNICA":
        assert resultado["coeficientes"] == [Fraction(1, 1001), Fraction(1, 1009)]
        assert resultado["coeficientes_texto"] == ["1/1001", "1/1009"]
        assert set(resultado["paso_verificacion"]) == CLAVES_VERIFICACION
        assert resultado["paso_verificacion"]["coincide"] is True
    else:
        assert resultado["paso_verificacion"] is None
        assert resultado["coeficientes"] is None
    if estado == "INFINITA":
        assert resultado["solucion_parametrica"] == ["3 - 2t", "t"]
        assert resultado["parametros_libres"] == ["c_2"]
    if estado == "SIN_SOLUCION":
        assert resultado["es_combinacion_lineal"] is False
        assert resultado["pasos_sustitucion_regresiva"] == []


@pytest.mark.parametrize("entrada", [
    {"orientation": "column", "data": [1, 2]},
    {"orientacion": "column", "datos": [1, 2]},
    {"orientacion": "row", "datos": [1, 2]},
    {"orientacion": "diagonal", "datos": [1, 2]},
    {"orientacion": "fila", "datos": "12"},
    {"orientacion": "columna", "datos": []},
    None,
])
def test_captura_rechaza_esquemas_ajenos(entrada):
    """Las claves antiguas y las formas inválidas nunca se aceptan como alternativas."""
    with pytest.raises(ValueError):
        construir_vector_desde_diccionario(entrada)


@pytest.mark.parametrize("operacion,estricto", [("add", False), ("subtract", False), ("otra", False), ("suma", "False")])
def test_opciones_invalidas_no_se_interpretan_como_resta(operacion, estricto):
    """El esquema canónico no acepta valores ni tipos de las opciones anteriores."""
    assert _calcular_binaria(operacion, estricto, "columna")["estado"] == "ERROR"


@pytest.mark.parametrize("metodo,carga", [
    ("procesar_suma_resta", {"operation": "add", "v1": _vector([1, 2]), "v2": _vector([3, 4])}),
    ("procesar_multiplicacion_escalar", {"scalar": 2, "v": _vector([1, 2])}),
    ("procesar_combinacion_lineal", {"b": _vector([1, 2]), "vectors": [_vector([1, 2])]}),
])
def test_controladores_rechazan_carga_anterior(metodo, carga):
    """Las tres operaciones rechazan las claves retiradas, sin compatibilidad dual."""
    respuesta = json.loads(getattr(ControladorOperacionesVectores, metodo)(json.dumps(carga)))
    assert respuesta["estado"] == "ERROR"
    assert respuesta["mensaje"] == "La carga contiene claves ajenas al contrato vectorial."


def test_panel_captura_y_herramienta_unicos(vista_vectorial_montada):
    """La captura conserva texto crudo y contexto/señales identifican la misma herramienta."""
    vista = vista_vectorial_montada
    vector = vista.panel_suma_resta.vectores["u"]
    assert set(vector) == {"orientacion", "celdas", "contenedor", "etiqueta_dimension", "boton_orientacion"}
    vector["celdas"] = {0: "1/1009", 1: "abc"}
    assert capturar_vectores({"u": vector}, 3) == {"u": _vector(["1/1009", "abc", "0"])}
    assert vista.obtener_contexto_ia().herramienta == vista.obtener_senales_ia().herramienta == "vectores"


def test_vistas_delegan_dominio_y_transferencia():
    """Las vistas no construyen números/matrices ni importan el preparador de dominio."""
    for ruta in (RAIZ / "src/frontend/vistas/operaciones_vectores").glob("*.py"):
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        llamadas = {nodo.func.id for nodo in ast.walk(arbol) if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)}
        assert not llamadas & {"Fraction", "Matriz", "float", "preparar_vectores_visualizador"}
    assert preparar_transferencia("suma_resta", {"u": _vector([1, 2]), "v": _vector([3, 4])}) == ([[1, 2], [3, 4]], "vectores")


def test_resultado_intermedio_largo_no_se_revalida_como_entrada():
    """Una fracción gaussiana de 302 caracteres sigue exacta en la tabla del reproductor."""
    numero = 10 ** 149 + 1
    carga = {"objetivo": _vector([1, 1]),
             "vectores": [_vector([numero, numero - 1]), _vector([numero - 2, numero - 4])]}
    resultado = json.loads(ControladorOperacionesVectores.procesar_combinacion_lineal(json.dumps(carga)))
    assert resultado["estado"] == "UNICA"
    paso = next(paso for paso in resultado["vista_pasos"]
                if any(len(celda) > 256 for fila in paso["matriz"]["datos"] for celda in fila))
    celda = next(celda for fila in paso["matriz"]["datos"] for celda in fila if len(celda) > 256)
    assert len(celda) == 302
    tabla = construir_tabla_paso_vectorial(paso, 2, ["c_1", "c_2"])
    assert str(abs(Fraction(celda).numerator)) in tabla
    assert str(Fraction(celda).denominator) in tabla


@pytest.mark.parametrize("nombre,esperado", [
    ("<img src=x>", "&lt;img src=x&gt;"),
    ("v_<script>x</script>", "v<sub>&lt;script&gt;x&lt;/script&gt;</sub>"),
    ("v_1", "v<sub>1</sub>"),
])
def test_etiquetas_vectoriales_se_escapan(nombre, esperado):
    """Las etiquetas arbitrarias no se interpretan como marcado en la cabecera."""
    assert _formatear_nombre_vector(nombre) == esperado
