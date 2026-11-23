"""Pruebas de captura, paridad, criterios y reproductor de subespacios por restricciones."""
import pytest

from src.frontend.controladores.algebra.operaciones_vectores import controlador_subespacios as ctrl
from src.frontend.controladores.algebra.operaciones_vectores.captura_restricciones import (
    ErrorCapturaRestricciones,
    interpretar_ecuaciones_restricciones,
    redactar_ecuaciones_restricciones,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MENSAJE_CALCULO_NO_VERIFICADO,
    VEREDICTO_CONJUNTO_VACIO,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.pasos_subespacios import (
    crear_reproductor_subespacios,
)


def _captura_matriz(matriz_a: list[list], vector_b: list, dimension: int) -> dict:
    return {
        "modo": "restricciones",
        "formato": "matriz",
        "dimension_ambiente": dimension,
        "matriz_a": matriz_a,
        "vector_b": vector_b,
    }


def _captura_ecuaciones(ecuaciones: str, dimension: int) -> dict:
    return {
        "modo": "restricciones",
        "formato": "ecuaciones",
        "dimension_ambiente": dimension,
        "ecuaciones": ecuaciones,
    }


def test_paridad_ejemplo_afin_matriz_y_ecuaciones():
    """El ejemplo afín oficial produce la misma salida exacta en Matriz y Ecuaciones."""
    por_matriz = ctrl.analizar_subespacio_desde_captura(_captura_matriz([["-1", "-1", "1"]], ["1"], 3))
    por_ecuaciones = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("-x1 - x2 + x3 = 1", 3))
    assert por_matriz == por_ecuaciones
    assert por_matriz["estado"] == "EXITO"
    assert por_matriz["clasificacion"] == "AFIN_NO_SUBESPACIO"
    assert por_matriz["es_subespacio"] is False
    assert por_matriz["es_espacio_vectorial"] is False
    assert "no es espacio vectorial con las operaciones usuales" in por_matriz["veredicto"].lower()
    assert por_matriz["dimension_afin"] == 2
    assert por_matriz["particular"] == ("-1", "0", "0")
    assert por_matriz["direcciones"] == (("-1", "1", "0"), ("1", "0", "1"))
    assert por_matriz["testigo"]["fila_visible"] == 1
    assert [criterio["estado"] for criterio in por_matriz["criterios"]] == ["No cumple"] * 3
    assert "A(p + p) = 2 ≠ 1" in por_matriz["criterios"][1]["resumen"]
    assert "A(2p) = 2 ≠ 1" in por_matriz["criterios"][2]["resumen"]


def test_variante_homogenea_y_recta_y_cero_en_r2():
    """Analiza la variante homogénea, la recta y = 0 sin perder x1 y el subespacio cero."""
    homogenea = ctrl.analizar_subespacio_desde_captura(_captura_matriz([["-1", "-1", "1"]], ["0"], 3))
    assert homogenea["clasificacion"] == "SUBESPACIO"
    assert homogenea["es_subespacio"] is True
    assert "espacio vectorial con las operaciones usuales" in homogenea["veredicto"].lower()
    assert homogenea["dimension"] == 2
    assert homogenea["variables_pivote"] == ("x1",)
    assert homogenea["variables_libres"] == ("x2", "x3")
    assert [criterio["estado"] for criterio in homogenea["criterios"]] == ["Cumple"] * 3

    recta = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("y = 0", 2))
    assert recta["dimension"] == 1
    assert recta["base"] == (("1", "0"),)

    cero = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("x = 0\ny = 0", 2))
    assert cero["es_subespacio_cero"] is True
    assert cero["base"] == ()


def test_sistema_incompatible_y_punto_afin_dimension_cero():
    """El conjunto vacío marca vacuidad y el punto afín conserva dimensión afín cero."""
    vacio = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("x = 0\nx = 1", 2))
    assert vacio["clasificacion"] == "VACIO_NO_SUBESPACIO"
    assert vacio["es_vacio"] is True
    assert VEREDICTO_CONJUNTO_VACIO in vacio["subtitulo_veredicto"]
    assert (vacio["rango"], vacio["rango_aumentada"]) == (1, 2)
    assert vacio["base"] is None
    assert vacio["testigo"]["tipo"] == "fila_contradictoria"
    assert [criterio["estado"] for criterio in vacio["criterios"]] == [
        "No cumple", "Se cumple vacuamente", "Se cumple vacuamente",
    ]

    punto = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("x = 2\ny = 3", 2))
    assert punto["clasificacion"] == "AFIN_NO_SUBESPACIO"
    assert punto["dimension_afin"] == 0
    assert punto["particular"] == ("2", "3")
    assert punto["direcciones"] == ()


@pytest.mark.parametrize("dimension,matriz_a,vector_b", [
    (2, [["0", "0"], ["0", "0"]], ["0", "1"]),
    (2, [["0", "1"]], ["0"]),
    (3, [["2/3", "0", "-1"]], ["1/5"]),
])
def test_ida_y_vuelta_matriz_ecuaciones_con_nulos_y_fracciones(dimension, matriz_a, vector_b):
    """Conserva filas nulas, columnas de ceros y fracciones exactas en ambos sentidos."""
    texto = redactar_ecuaciones_restricciones(matriz_a, vector_b)
    interpretada = interpretar_ecuaciones_restricciones(texto, dimension)
    assert interpretada.dimension_ambiente == dimension
    assert interpretada.matriz_a == matriz_a
    assert interpretada.vector_b == vector_b


def test_subindices_unicode_alias_y_solo_constantes():
    """Acepta subíndices Unicode y guía el uso de 0x1 ante ecuaciones sin variables."""
    capturada = interpretar_ecuaciones_restricciones("x₁ - x₂ = 0", 2)
    assert capturada.matriz_a == [["1", "-1"]]
    assert capturada.vector_b == ["0"]
    with pytest.raises(ErrorCapturaRestricciones, match="0x1"):
        interpretar_ecuaciones_restricciones("0 = 1", 2)


@pytest.mark.parametrize("texto,dimension", [
    ("z = 0", 2),
    ("x = 0", 4),
    ("x4 = 0", 3),
    ("x + x1 = 0", 2),
    ("y + x2 = 1", 3),
    ("x1 + x_1 = 0", 2),
])
def test_rechaza_alias_fuera_de_rango_y_colisiones(texto, dimension):
    """Rechaza coordenadas fuera de ℝⁿ, alias en dimensión incorrecta y colisiones."""
    with pytest.raises(ErrorCapturaRestricciones):
        interpretar_ecuaciones_restricciones(texto, dimension)


def test_restricciones_invalidas_y_vacias_ubican_diagnostico():
    """Distingue matriz en blanco de celda inválida con coordenadas desde 1."""
    vacia = ctrl.analizar_subespacio_desde_captura(_captura_matriz([["", ""]], [""], 2))
    assert vacia["estado"] == "ERROR"
    assert vacia["codigo"] == "ENTRADA_INVALIDA"

    invalida = ctrl.analizar_subespacio_desde_captura(_captura_matriz([["1", "abc", "0"]], ["1"], 3))
    assert invalida["estado"] == "ERROR"
    assert invalida["codigo"] == "ENTRADA_INVALIDA"
    assert invalida["diagnostico"]["campo"] == "matriz_a"
    assert invalida["diagnostico"]["fila"] == 1
    assert invalida["diagnostico"]["columna"] == 2


@pytest.mark.parametrize("codigo", ["VERIFICACION_INCONSISTENTE", "ERROR_INTERNO"])
def test_errores_internos_restricciones_no_filtran_detalles(monkeypatch, codigo):
    """Oculta detalles internos y evita publicar trazas parciales o veredictos falsos."""
    monkeypatch.setattr(
        ctrl,
        "analizar_subespacio",
        lambda _entrada: {
            "estado": "ERROR",
            "modo": "restricciones",
            "codigo": codigo,
            "mensaje": "Traceback secreto interno",
            "dimension_ambiente": 3,
        },
    )
    resultado = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("-x1 - x2 + x3 = 1", 3))
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"] == MENSAJE_CALCULO_NO_VERIFICADO
    assert "Traceback" not in resultado["mensaje"]
    assert resultado["es_subespacio"] is None
    assert resultado["pasos"] == ()
    assert resultado["comprobaciones"] == ()


def test_reproductor_restricciones_separa_grupos_y_criterios():
    """Separa reducción de [A|b], lectura de solución/testigo, criterios y motor."""
    resultado = ctrl.analizar_subespacio_desde_captura(_captura_ecuaciones("-x1 - x2 + x3 = 1", 3))
    reproductor, indices = crear_reproductor_subespacios(resultado)
    assert [grupo.tipo for grupo in reproductor.grupos] == ["eliminacion", "final", "planteamiento", "verificacion"]
    assert set(indices) == {"origen", "suma", "escalar"}
    assert len(set(indices.values())) == 3
    for clave, indice in indices.items():
        paso = reproductor.pasos[indice]
        assert paso.cuerpo[0] == "teorema"
        assert paso.cuerpo[1]["clave"] == clave
