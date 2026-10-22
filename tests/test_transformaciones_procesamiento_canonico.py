"""Procesamiento público de una transformación identidad mediante el contrato canónico."""
import json

from src.frontend.controladores.operaciones_matrices.controlador_transformaciones import ControladorTransformaciones


def test_procesar_identidad_con_entrada_serializada():
    """Conserva la entrada identidad y el resultado exitoso de la operación pública."""
    carga = json.dumps({'matriz_transformacion': [['1', '0'], ['0', '1']]})
    resultado = json.loads(ControladorTransformaciones.procesar(carga))
    assert resultado['estado'] == 'EXITO'
    assert not hasattr(ControladorTransformaciones, 'process')
