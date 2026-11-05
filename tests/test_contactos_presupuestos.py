"""Fronteras de los presupuestos auxiliares y compatibilidad de sus contratos."""
import json
from dataclasses import asdict

from src.backend.resolutores.raices.contrato_exploracion import (
    CandidatoExploracion, EntradaExploracion, EvidenciaContacto, ResultadoExploracion,
)
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
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


def test_maximo_combinado_malla_y_auxiliares(monkeypatch):
    """El máximo de 4097 muestras y 512 sondeos está acotado a 4609 evaluaciones reales."""
    from src.backend.resolutores.raices import evaluacion_exploracion
    original = evaluacion_exploracion.evaluar
    llamadas = []
    def evaluar_contada(funcion, abscisa):
        """Cuenta intentos reales sin evaluar por segunda vez."""
        llamadas.append(abscisa)
        return original(funcion, abscisa)
    monkeypatch.setattr(evaluacion_exploracion, "evaluar", evaluar_contada)
    entrada = EntradaExploracion("sin(x-.013)**2+1e-10", 0, 4096 * .05, .05)
    resultado = explorar_intervalos(entrada)
    assert resultado.evaluaciones == 4097 and resultado.evaluaciones_refinamiento == 512
    assert len(llamadas) == 4609 and resultado.refinamiento_agotado
