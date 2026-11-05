"""Fronteras de los presupuestos auxiliares y compatibilidad de sus contratos."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_exploracion import (
    CandidatoExploracion, EvidenciaContacto, ResultadoExploracion,
)
from src.backend.resolutores.raices.limites_exploracion import (
    EVALUACIONES_POR_REFINAMIENTO, MAXIMO_EVALUACIONES_CONTACTO,
    MAXIMO_EVALUACIONES_EXPLORACION, MAXIMO_EVALUACIONES_REFINAMIENTO,
    MAXIMO_REFINAMIENTOS_CONTACTO, MAXIMO_REGISTROS_EXPLORACION,
)


def test_limites_de_refinamiento_independientes_de_la_malla():
    """Los doce pasos de dos evaluaciones tienen cota individual 24 y auxiliar global 512."""
    assert MAXIMO_REFINAMIENTOS_CONTACTO == 12
    assert EVALUACIONES_POR_REFINAMIENTO == 2
    assert MAXIMO_EVALUACIONES_CONTACTO == 24
    assert MAXIMO_EVALUACIONES_REFINAMIENTO == 512
    assert MAXIMO_EVALUACIONES_EXPLORACION == 4097 and MAXIMO_REGISTROS_EXPLORACION == 256


def test_contrato_antiguo_y_evidencia_son_aditivos_y_serializables():
    """Los argumentos previos conservan su orden y los contadores auxiliares parten de cero."""
    candidato = CandidatoExploracion("posible_contacto", (-1, 1), 0, .01, "No certifica raíz.")
    resultado = ResultadoExploracion((candidato,), 3)
    assert candidato.evidencia_contacto is None
    assert resultado.evaluaciones_refinamiento == resultado.refinamientos == 0
    assert not resultado.refinamiento_agotado
    evidencia = EvidenciaContacto(.01, .5, 24, 12, "limite_refinamientos")
    assert json.loads(json.dumps(asdict(evidencia), allow_nan=False))["evaluaciones"] == 24
