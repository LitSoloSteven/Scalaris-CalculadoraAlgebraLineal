"""Contrato rectangular del dominio y compatibilidad del validador cuadrado."""
from copy import deepcopy
import pytest

from src.backend.constantes import LONGITUD_MAXIMA_CELDA, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS
from src.backend.utilidades.transferencias import validar_carga_matriz, validar_carga_matriz_rectangular


def _carga(datos):
    return {"version": 1, "tipo": "matriz_a", "origen": "matrices", "datos": datos}


def test_rectangulo_exacto_conserva_texto_y_no_muta_carga():
    """El éxito conserva signos, decimales y fracciones sin normalizar la entrada."""
    datos = [["1/1001", "0", "-2/3"], ["+4", "5.00", "6"]]
    carga = _carga(datos)
    anterior = deepcopy(carga)
    assert validar_carga_matriz_rectangular(carga, filas_maximas=2, columnas_maximas=3) == (datos, None)
    assert carga == anterior
    assert validar_carga_matriz(carga, dimension_maxima=50) == (None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("datos", [None, [], [None], [[]], ["12"], [["1"], None],
                                  [["1", "2"], ["3"]], [["1"], ("2",)], ([],), "12", 1])
def test_estructuras_invalidas_devuelven_error_sin_excepcion(datos):
    """Raíces y filas inválidas se rechazan antes de leer sus celdas."""
    assert validar_carga_matriz_rectangular(_carga(datos), filas_maximas=2, columnas_maximas=3) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("valor", ["texto", "1/0", "", "1e3", "<img>", None, True, 1,
                                  "9" * (LONGITUD_MAXIMA_CELDA + 1)])
def test_celdas_invalidas_no_se_sanean_ni_modifican(valor):
    """La transferencia rechaza contenido inválido sin filtrar sus caracteres."""
    carga = _carga([[valor]])
    anterior = deepcopy(carga)
    assert validar_carga_matriz_rectangular(carga, filas_maximas=2, columnas_maximas=3) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)
    assert carga == anterior


@pytest.mark.parametrize("filas,columnas", [(3, 1), (1, 4), (3, 4)])
def test_excesos_de_cada_eje_tienen_mensaje_exacto(filas, columnas):
    """El rechazo identifica la forma real y ambos máximos sin saltos de línea."""
    carga = _carga([["1"] * columnas for _ in range(filas)])
    esperado = (f"La matriz es de {filas}×{columnas} y esta herramienta admite hasta "
                "2×3. Empezamos con la herramienta vacía.")
    assert validar_carga_matriz_rectangular(carga, filas_maximas=2, columnas_maximas=3) == (None, esperado)


@pytest.mark.parametrize("maximo", [True, False, 0, -1, "2", 2.0, None, [], {}])
@pytest.mark.parametrize("eje", ["filas_maximas", "columnas_maximas"])
def test_configuracion_invalida_devuelve_error_controlado(maximo, eje):
    """Ningún eje acepta booleanos, cero, negativos ni tipos ajenos a int."""
    limites = {"filas_maximas": 2, "columnas_maximas": 3, eje: maximo}
    assert validar_carga_matriz_rectangular(_carga([["1"]]), **limites) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("clave,valor", [("version", True), ("version", 2), ("tipo", "sistema"),
                                        ("origen", None), ("extra", "valor")])
def test_envoltura_canonica_no_admite_tipos_ni_claves_ajenas(clave, valor):
    """La ampliación usa el mismo sobre exacto que el contrato cuadrado."""
    carga = {**_carga([["1"]]), clave: valor}
    assert validar_carga_matriz_rectangular(carga, filas_maximas=2, columnas_maximas=3) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


@pytest.mark.parametrize("carga", [None, [], "matriz", 0, {}])
def test_envolturas_ausentes_no_provocan_excepciones(carga):
    """Una carga ajena al diccionario canónico produce el error compartido."""
    assert validar_carga_matriz_rectangular(carga, filas_maximas=2, columnas_maximas=3) == (
        None, MENSAJE_TRANSFERENCIA_DATOS_INVALIDOS)


def test_celda_en_longitud_maxima_y_ejes_unitarios_son_validos():
    """Se aceptan los límites inclusivos de texto y matrices de una fila o columna."""
    valor = "0." + "0" * (LONGITUD_MAXIMA_CELDA - 3) + "1"
    for datos in ([[valor, "0"]], [[valor], ["0"]], [["1"]]):
        assert validar_carga_matriz_rectangular(_carga(datos), filas_maximas=2, columnas_maximas=2) == (datos, None)
