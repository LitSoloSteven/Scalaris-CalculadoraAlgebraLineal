"""Preparación y controles comunes del foco de una operación matricial."""
from src.backend.resolutores.operaciones_matrices.evaluador import EvaluadorExpresionesMatriciales
from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import ControladorOperacionesMatrices


def evaluar_foco_matriz(expresion, matrices):
    """Evalúa las mismas matrices y exige un único paso antes de construir su foco."""
    resultado = EvaluadorExpresionesMatriciales().evaluar(expresion, matrices)
    assert resultado['estado'] == 'EXITO'
    assert len(resultado['pasos_segmento']) == 1
    paso = resultado['pasos_segmento'][0]
    foco = ControladorOperacionesMatrices.construir_foco_paso(paso, 1, 1)
    assert foco['indice'] == 1
    assert foco['total'] == 1
    assert foco['tipo'] == 'otro'
    return paso, foco


def comprobar_ejemplo_foco(foco, paso, comienzo):
    """Conserva forma, existencia, brevedad y diferencia respecto al detalle completo."""
    assert foco['detalle'] is not None
    assert foco['detalle']['forma'] == '2×2'
    assert 'ejemplo' in foco['detalle']
    assert foco['detalle']['ejemplo'].startswith(comienzo)
    assert len(foco['detalle']['ejemplo']) <= 120
    assert foco['detalle']['ejemplo'] != paso['pasos_celda_a_celda'][0]['descripcion']
