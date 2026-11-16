"""Limites, estados de error y contrato serializable del analisis de subespacios."""
import json
import math
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.captura_subespacios import (
    capturar_generadores,
    capturar_restricciones,
)
from src.backend.resolutores.operaciones_vectores.comprobacion_subespacios import (
    verificar_base_generadores,
)
from src.backend.resolutores.operaciones_vectores.contrato_subespacios import (
    ErrorCapturaSubespacio,
    ErrorVerificacionSubespacio,
)
from src.backend.resolutores.operaciones_vectores.subespacios import analizar_subespacio
from src.frontend.controladores.operaciones_matrices.codificador import CodificadorMatriz

CLAVES_RESULTADO = {
    "estado", "modo", "clasificacion", "codigo", "mensaje", "dimension_ambiente",
    "es_subespacio", "contiene_origen", "es_vacio", "rango", "rango_aumentada",
    "base", "dimension", "indices_generadores_base", "etiquetas_generadores_base",
    "columnas_pivote", "columnas_libres", "particular", "direcciones",
    "dimension_afin", "testigo", "matriz_original", "matriz_reducida", "pasos",
    "comprobaciones",
}


def _generadores(datos, etiquetas=None):
    """Devuelve una entrada tipada de generadores columna."""
    nombres = etiquetas or [f"v_{indice + 1}" for indice in range(len(datos))]
    return {
        "modo": "generadores",
        "dimension_ambiente": len(datos[0]),
        "generadores": tuple(
            Matriz(len(dato), 1, [[valor] for valor in dato]) for dato in datos
        ),
        "etiquetas": tuple(nombres),
    }


def test_resultado_siempre_tiene_las_mismas_claves_en_todos_los_estados():
    """Exito generador, nucleo, afin, vacio y error comparten exactamente el contrato."""
    resultados = [
        analizar_subespacio(_generadores([(1, 0), (0, 1)])),
        analizar_subespacio(capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 2,
            "matriz_a": [[1, 1]], "vector_b": [0],
        })),
        analizar_subespacio(capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 2,
            "matriz_a": [[1, 1]], "vector_b": [1],
        })),
        analizar_subespacio(capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 2,
            "matriz_a": [[1, 0], [1, 0]], "vector_b": [1, 2],
        })),
        analizar_subespacio({}),
    ]
    assert [set(resultado) for resultado in resultados] == [CLAVES_RESULTADO] * 5


def test_entradas_malformadas_devuelven_error_sin_traceback():
    """La API publica devuelve ERROR granular para objetos, modos, cantidades y tipos ajenos."""
    entradas = [
        None,
        {},
        {"modo": "otro", "dimension_ambiente": 2},
        {"modo": "generadores", "dimension_ambiente": 3,
         "generadores": (), "etiquetas": ()},
        {"modo": "generadores", "dimension_ambiente": 3,
         "generadores": (Matriz(2, 1, [[1], [2]]),), "etiquetas": ("v_1",)},
        {"modo": "generadores", "dimension_ambiente": 3,
         "generadores": tuple(Matriz(3, 1, [[0], [0], [0]]) for _ in range(11)),
         "etiquetas": tuple(f"v_{indice}" for indice in range(11))},
        {"modo": "restricciones", "dimension_ambiente": 3,
         "matriz_a": [[1, 0, 0]], "vector_b": [0]},
    ]
    for entrada in entradas:
        resultado = analizar_subespacio(entrada)
        assert resultado["estado"] == "ERROR"
        assert resultado["codigo"] == "ENTRADA_INVALIDA"
        assert resultado["base"] is None
        assert resultado["pasos"] == ()
        assert "Traceback" not in resultado["mensaje"]


def test_matriz_con_booleano_se_rechaza_aunque_el_modelo_lo_almacene():
    """Un booleano no se interpreta como uno en una entrada directa del dominio."""
    resultado = analizar_subespacio({
        "modo": "restricciones",
        "dimension_ambiente": 1,
        "matriz_a": Matriz(1, 1, [[True]]),
        "vector_b": (0,),
    })
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"


@pytest.mark.parametrize("etiqueta", ["x" * 65, "v\x00", "v\u200b"])
def test_entrada_tipada_rechaza_etiquetas_largas_o_invisibles(etiqueta):
    """El contrato revalida las etiquetas aunque la entrada no pase por la captura JSON."""
    resultado = analizar_subespacio(_generadores([(1,)], [etiqueta]))
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert resultado["base"] is None


def test_entrada_tipada_admite_una_etiqueta_de_longitud_maxima():
    """El limite de 64 caracteres es inclusivo y no rechaza etiquetas legitimas."""
    resultado = analizar_subespacio(_generadores([(1,)], ["v" * 64]))
    assert resultado["estado"] == "EXITO"
    assert resultado["etiquetas_generadores_base"] == ("v" * 64,)


def test_verificador_de_base_rechaza_indices_fuera_de_rango_o_desalineados():
    """El oraculo de base no puede truncar indices: longitudes, unicidad y rango coinciden."""
    generadores = (Matriz(1, 1, [[1]]), Matriz(1, 1, [[2]]))
    base = ((Fraction(1),),)
    for indices in ((0, 1), (0, 0), (2,)):
        with pytest.raises(ErrorVerificacionSubespacio):
            verificar_base_generadores(generadores, base, indices)


def test_limites_de_dimension_uno_y_diez():
    """La dimension ambiente admite los extremos uno y diez en ambos modos."""
    uno = analizar_subespacio(_generadores([(1,), (2,)]))
    diez = analizar_subespacio(_generadores([tuple(int(fila == columna) for columna in range(10))
                                             for fila in range(10)]))
    assert uno["dimension"] == 1
    assert uno["base"] == ((1,),)
    assert diez["dimension"] == 10
    assert diez["base"] == tuple(
        tuple(int(fila == columna) for columna in range(10)) for fila in range(10)
    )


def test_captura_vacia_no_es_el_subespacio_cero_explicito():
    """Sin generadores no hay ejercicio; dos generadores nulos si son un ejercicio de {0}."""
    with pytest.raises(ErrorCapturaSubespacio):
        capturar_generadores({"modo": "generadores", "dimension_ambiente": 3, "vectores": {}})
    cero = analizar_subespacio(_generadores([(0, 0, 0), (0, 0, 0)]))
    assert cero["estado"] == "EXITO"
    assert cero["base"] == ()
    assert cero["es_vacio"] is False


@pytest.mark.parametrize("celda", [
    True, "1/0", "nan", "inf", float("nan"), float("inf"), None, {"valor": 1},
])
def test_captura_rechaza_valores_no_exactos(celda):
    """Booleanos, divisiones invalidas, no finitos, nulos y objetos no son escalares exactos."""
    with pytest.raises(ErrorCapturaSubespacio):
        capturar_generadores({
            "modo": "generadores", "dimension_ambiente": 1,
            "vectores": {"v_1": {"datos": [celda]}},
        })


def test_resultado_serializa_fracciones_y_matrices_con_el_codificador_comun():
    """La frontera JSON conserva fracciones como texto y matrices como objetos canonicos."""
    resultado = analizar_subespacio(capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 2,
        "matriz_a": [["1/3", 1]], "vector_b": ["1/7"],
    }))
    serializado = json.loads(json.dumps(resultado, cls=CodificadorMatriz, ensure_ascii=False))
    assert serializado["base"] is None
    assert serializado["particular"] == ["3/7", "0"]
    assert serializado["direcciones"] == [["-3", "1"]]
    assert serializado["matriz_original"]["columnas"] == 3
    assert serializado["matriz_reducida"]["filas"] == 1


def test_fallo_de_verificacion_interna_devuelve_error_diagnosticado(monkeypatch):
    """Una comprobacion que no coincide no se convierte en un resultado valido."""
    modulo = "src.backend.resolutores.operaciones_vectores.comprobacion_subespacios"
    monkeypatch.setattr(f"{modulo}.comprobar_familia", lambda *argumentos: {
        "coincide": False, "filas": [], "pasos_latex": [],
    })
    resultado = analizar_subespacio(capturar_restricciones({
        "modo": "restricciones", "dimension_ambiente": 2,
        "matriz_a": [[1, 1]], "vector_b": [0],
    }))
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "VERIFICACION_INCONSISTENTE"
    assert resultado["base"] is None


def test_restricciones_rechazan_no_finitos_y_fuera_de_limite():
    """El parser compartido rechaza NaN e infinito y la captura limita filas y columnas."""
    for valor in (math.nan, math.inf, "nan", "inf"):
        with pytest.raises(ErrorCapturaSubespacio):
            capturar_restricciones({
                "modo": "restricciones", "dimension_ambiente": 1,
                "matriz_a": [[valor]], "vector_b": [0],
            })
    with pytest.raises(ErrorCapturaSubespacio):
        capturar_restricciones({
            "modo": "restricciones", "dimension_ambiente": 11,
            "matriz_a": [[0] * 11], "vector_b": [0],
        })
