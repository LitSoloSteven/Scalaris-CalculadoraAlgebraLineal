"""Pruebas de captura, presentación exacta y reproductor de subespacios por generadores."""
from fractions import Fraction
import math

import pytest

from src.frontend.componentes.captura.vectores.captura_vectores import _formatear_nombre_vector
from src.frontend.controladores.algebra.operaciones_vectores import controlador_subespacios as ctrl
from src.frontend.controladores.algebra.operaciones_vectores.presentacion_subespacios import (
    presentar_resultado_subespacio,
)
from src.frontend.nucleo.textos.textos_espacios_subespacios import (
    MENSAJE_CALCULO_NO_VERIFICADO,
    NOTA_DIMENSION_SUPERIOR,
    VEREDICTO_SUBESPACIO_CERO,
)
from src.frontend.vistas.algebra.operaciones_vectores.panel.pasos_subespacios import (
    crear_reproductor_subespacios,
)


def _captura(vectores: dict[str, list], dimension: int) -> dict:
    return {
        "modo": "generadores",
        "dimension_ambiente": dimension,
        "vectores": {
            etiqueta: {"orientacion": "columna", "datos": list(componentes)}
            for etiqueta, componentes in vectores.items()
        },
    }


def test_ejemplo_generadores_devuelve_espacio_vectorial_base_y_relacion():
    """El ejemplo oficial genera un plano en R^3 con base (v_1, v_2) y v_3 = v_1 + v_2."""
    resultado = ctrl.analizar_generadores_desde_captura(_captura(ctrl.ejemplo_generadores(), 3))
    assert resultado["estado"] == "EXITO"
    assert "espacio vectorial con las operaciones usuales" in resultado["veredicto"].lower()
    assert "subespacio de ℝ³" in resultado["veredicto"]
    assert resultado["rango"] == 2
    assert resultado["dimension"] == 2
    assert resultado["es_subespacio_cero"] is False
    assert resultado["etiquetas_generadores_base"] == ("v_1", "v_2")
    assert resultado["base"] == (("1", "0", "1"), ("0", "1", "1"))
    assert len(resultado["dependencias"]) == 1
    assert resultado["dependencias"][0]["respaldada"] is True
    assert resultado["dependencias"][0]["texto"] == "v_3 = v_1 + v_2"


def test_dependencia_no_respaldada_por_reduccion_omite_combinacion(monkeypatch):
    """Solo muestra la relación exacta si la forma escalonada reducida la respalda."""
    original = ctrl.analizar_subespacio(
        ctrl.capturar_generadores(_captura(ctrl.ejemplo_generadores(), 3))
    )
    alterado = dict(original)
    reducida = original["matriz_reducida"].clonar()
    reducida.establecer(2, 0, Fraction(5))
    alterado["matriz_reducida"] = reducida
    resultado = presentar_resultado_subespacio(alterado, etiquetas=("v_1", "v_2", "v_3"))
    assert resultado["dependencias"][0]["respaldada"] is False
    assert "v_1 + v_2" not in resultado["dependencias"][0]["texto"]
    assert "v_3" in resultado["dependencias"][0]["texto"]


def test_familia_independiente_dimension_uno_y_mayor_que_tres():
    """Cubre familia sin redundantes, R^1 y dimensión ambiente mayor a tres."""
    independiente = ctrl.analizar_generadores_desde_captura(
        _captura({"v_1": ["1", "0"], "v_2": ["0", "2"]}, 2)
    )
    assert independiente["dimension"] == 2
    assert independiente["dependencias"] == ()

    uno = ctrl.analizar_generadores_desde_captura(_captura({"v_1": ["3"]}, 1))
    assert uno["dimension"] == 1
    assert "ℝ¹" in uno["veredicto"]

    cuatro = ctrl.analizar_generadores_desde_captura(
        _captura({"v_1": ["1", "0", "0", "0"], "v_2": ["0", "1", "0", "1"]}, 4)
    )
    assert cuatro["dimension"] == 2
    assert cuatro["dimension_ambiente"] == 4
    assert NOTA_DIMENSION_SUPERIOR in cuatro["descripcion_geometrica"]


def test_vectores_cero_explicitos_devuelven_subespacio_cero():
    """Un conjunto de vectores cero explícitos produce Subespacio cero y base vacía."""
    resultado = ctrl.analizar_generadores_desde_captura(
        _captura({"v_1": ["0", "0", "0"], "v_2": ["0", "0", "0"]}, 3)
    )
    assert resultado["estado"] == "EXITO"
    assert resultado["es_subespacio_cero"] is True
    assert resultado["dimension"] == 0
    assert resultado["base"] == ()
    assert VEREDICTO_SUBESPACIO_CERO in resultado["subtitulo_veredicto"]


@pytest.mark.parametrize(
    "vectores,etiqueta_esperada,componente_esperada",
    [
        ({"v_1": ["", "", ""]}, None, None),
        ({"v_1": ["1", "", "0"]}, "v_1", 1),
        ({"v_1": ["1", "abc", "0"]}, "v_1", 1),
        ({"v_1": ["1", 1.5, "0"]}, "v_1", 1),
        ({"v_1": ["1", True, "0"]}, "v_1", 1),
    ],
)
def test_captura_vacia_parcial_y_componentes_invalidas(
    vectores, etiqueta_esperada, componente_esperada
):
    """Distingue captura vacía, celda en blanco y valor inválido con diagnóstico ubicado."""
    resultado = ctrl.analizar_generadores_desde_captura(_captura(vectores, 3))
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert resultado["diagnostico"]["etiqueta"] == etiqueta_esperada
    assert resultado["diagnostico"]["componente"] == componente_esperada


def test_etiquetas_largas_y_caracteres_especiales_se_escapan():
    """Preserva etiquetas largas y escapa marcado HTML en cabeceras vectoriales."""
    etiqueta_larga = "generador_extenso_" + "a" * 35
    resultado = ctrl.analizar_generadores_desde_captura(
        _captura({etiqueta_larga: ["1", "0"]}, 2)
    )
    assert resultado["etiquetas_generadores_base"] == (etiqueta_larga,)
    assert _formatear_nombre_vector("generador_largo") == "generador<sub>largo</sub>"
    assert "&lt;script&gt;" in _formatear_nombre_vector("v_<script>1</script>")


def test_reproductor_separa_teorema_verificaciones_y_racionales_largos():
    """Alinea la matriz de pasos, separa teorema de motor y tolera racionales extensos."""
    resultado = ctrl.analizar_generadores_desde_captura(_captura(ctrl.ejemplo_generadores(), 3))
    reproductor, indices = crear_reproductor_subespacios(resultado)
    assert set(indices) == {"origen", "suma", "escalar"}
    assert len(set(indices.values())) == 3
    for clave, indice in indices.items():
        paso = reproductor.pasos[indice]
        assert paso.cuerpo[0] == "teorema"
        assert paso.cuerpo[1]["clave"] == clave
    assert resultado["pasos"][0]["matriz"] == resultado["matriz_original"]
    assert any(grupo.tipo == "verificacion" for grupo in reproductor.grupos)

    factor = math.factorial(110) * 10**71
    vectores_cauchy = {
        f"v_{columna + 1}": [f"1/{(1 + 10 * fila + columna) * factor + 1}" for fila in range(10)]
        for columna in range(10)
    }
    resultado_largo = ctrl.analizar_generadores_desde_captura(_captura(vectores_cauchy, 10))
    assert resultado_largo["estado"] == "EXITO"
    assert resultado_largo["dimension"] == 10
    reproductor_largo, _ = crear_reproductor_subespacios(resultado_largo)
    assert len(reproductor_largo.pasos) > 0


@pytest.mark.parametrize("codigo", ["VERIFICACION_INCONSISTENTE", "ERROR_INTERNO"])
def test_errores_internos_no_filtran_detalles(monkeypatch, codigo):
    """Degrada fallos internos sin exponer trazas ni generar pasos parciales."""
    monkeypatch.setattr(
        ctrl,
        "analizar_subespacio",
        lambda _entrada: {
            "estado": "ERROR",
            "modo": "generadores",
            "codigo": codigo,
            "mensaje": "Detalle interno Traceback secreto",
            "dimension_ambiente": 3,
        },
    )
    resultado = ctrl.analizar_generadores_desde_captura(_captura(ctrl.ejemplo_generadores(), 3))
    assert resultado["estado"] == "ERROR"
    assert resultado["mensaje"] == MENSAJE_CALCULO_NO_VERIFICADO
    assert "Traceback" not in resultado["mensaje"]
    assert resultado["pasos"] == ()
    assert resultado["comprobaciones"] == ()
