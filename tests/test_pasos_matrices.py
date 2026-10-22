"""Adaptación de operaciones matriciales al reproductor de pasos."""
from tests.comun_entradas import copiar_entrada_prueba

import json
from tests.comun_textos import PATRONES_VOSEO, comprobar_textos_sobrios

from src.frontend.controladores.operaciones_matrices import (
    ControladorOperacionesMatrices,
)
from src.frontend.vistas.operaciones_matrices._pasos_reproductor import construir_pasos_matrices


def _evaluar(expresion: str, matrices: dict) -> dict:
    """Evalúa la expresión matricial con el controlador y devuelve el dict deserializado."""
    return json.loads(ControladorOperacionesMatrices.procesar_expresion(expresion, json.dumps(matrices)))


def test_expresion_compleja_produce_pasos_con_etiquetas_y_grupo_por_suboperacion():
    """'2A - B(C - D^T)' produce pasos con tipo 'operacion', etiquetas correctas y un grupo por suboperación."""
    matrices = copiar_entrada_prueba('matrices_expresion')
    res = _evaluar("2A - B(C - D^T)", matrices)
    assert res["estado"] == "EXITO"
    assert len(res.get("pasos_segmento", [])) > 1

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == len(res["pasos_segmento"])
    assert len(grupos) == len(pasos)

    etiquetas_validas = {"Suma", "Resta", "Multiplicación de Matrices",
                        "Multiplicación Escalar", "Transposición", "Negación"}
    for i, paso in enumerate(pasos):
        assert paso.tipo == "operacion"
        assert paso.etiqueta_tipo in etiquetas_validas
        assert paso.indice == i
        assert paso.indice_grupo == i
        assert paso.meta_explicar is not None
        assert paso.meta_explicar["indice"] == i + 1
        assert paso.meta_explicar["total"] == len(pasos)
        assert paso.meta_explicar["tipo"] == "otro"
        assert paso.cuerpo == res["pasos_segmento"][i]

    for i, grupo in enumerate(grupos):
        assert grupo.tipo == "operacion"
        assert grupo.indices_pasos == (i,)
        assert grupo.titulo == pasos[i].descripcion
        assert grupo.resumen == "1 operación"


def test_expresion_de_una_sola_operacion_produce_un_paso_y_un_grupo():
    """Una expresión con una sola suboperación genera un único paso y un único grupo."""
    matrices = {
        "A": {"filas": 2, "columnas": 2, "datos": [["1", "0"], ["0", "1"]]},
        "B": {"filas": 2, "columnas": 2, "datos": [["2", "3"], ["4", "5"]]},
    }
    res = _evaluar("A + B", matrices)
    assert res["estado"] == "EXITO"
    assert len(res.get("pasos_segmento", [])) == 1

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == 1
    assert len(grupos) == 1

    paso = pasos[0]
    assert paso.tipo == "operacion"
    assert paso.etiqueta_tipo == "Suma"
    assert paso.indice == 0
    assert paso.indice_grupo == 0

    grupo = grupos[0]
    assert grupo.titulo == "Operaciones de la expresión"
    assert grupo.resumen == "1 operación"
    assert grupo.tipo == "operacion"
    assert grupo.indices_pasos == (0,)


def test_transposicion_sin_desglose_por_celdas():
    """La transposición no incluye desglose celda a celda."""
    matrices = {
        "A": {"filas": 2, "columnas": 3, "datos": [["1", "2", "3"], ["4", "5", "6"]]},
    }
    res = _evaluar("A^T", matrices)
    assert res["estado"] == "EXITO"

    pasos, grupos = construir_pasos_matrices(res)
    assert len(pasos) == 1
    paso = pasos[0]
    assert paso.etiqueta_tipo == "Transposición"
    cuerpo = paso.cuerpo
    assert not cuerpo.get("pasos_celda_a_celda")
    assert "filas pasan a ser columnas" in paso.explicacion.lower()


def test_error_de_dimensiones_no_genera_pasos():
    """Si la expresión falla por incompatibilidad de dimensiones, no se generan pasos."""
    matrices = {
        "A": {"filas": 2, "columnas": 2, "datos": [["1", "2"], ["3", "4"]]},
        "B": {"filas": 3, "columnas": 3, "datos": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]},
    }
    res = _evaluar("A + B", matrices)
    assert res["estado"] == "ERROR"
    assert "dimens" in res["mensaje"].lower() or "tamaño" in res["mensaje"].lower()

    pasos, grupos = construir_pasos_matrices(res)
    assert pasos == ()
    assert grupos == ()


def test_textos_matriciales_sin_raya_larga_ni_voseo():
    """Las descripciones y explicaciones conservan un español directo."""
    matrices = copiar_entrada_prueba('matrices_expresion')
    expresiones = ["2A - B(C - D^T)", "A + B", "-A", "3 * A", "A * B", "A^T"]
    for expresion in expresiones:
        resultado = _evaluar(expresion, matrices)
        pasos, grupos = construir_pasos_matrices(resultado)
        for paso in pasos:
            comprobar_textos_sobrios((paso.descripcion, paso.explicacion), PATRONES_VOSEO)
        for grupo in grupos:
            comprobar_textos_sobrios((grupo.titulo, grupo.resumen), PATRONES_VOSEO, "en grupo")
