"""Cierres ordinarios y restricciones observadas conservan su significado."""
import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import CONTINUIDAD_CONDICIONAL, EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada


@pytest.mark.parametrize("expresion,intervalo,precision", [
    ("1e300*(x-.123456789)", (-1, 1), 4), ("1e-300*(x-.123456789)", (-1, 1), 4),
    ("1e200*(exp(x)-2)", (0, 2), 4), ("1e200*sin(12*x)", (.1, .4), 4),
    ("tanh(1e20*(x-.1))", (-1, 1), 4), ("x/(x*x+1e-14)", (-.13, .83), 12),
])
def test_magnitudes_y_transiciones_continuas_no_bastan(expresion, intervalo, precision):
    """Una escala extrema, saturación o crecimiento transitorio no basta para el diagnóstico."""
    resultado = biseccion(EntradaBiseccion(expresion, *intervalo, precision))
    assert resultado.estado == "EXITO" and len(resultado.iteraciones) >= 6
    assert "evidencia_discontinuidad" not in resultado.diagnostico
    assert resultado.metricas["continuidad"] == CONTINUIDAD_CONDICIONAL


def test_cierre_temprano_sin_evidencia_suficiente():
    """Cinco filas conservan el conteo solicitado y la garantía condicionada."""
    entrada = EntradaBiseccion("1/(x*x-.2)", 0, 1, 4, criterio=CriterioParada("iteraciones", 5))
    resultado = biseccion(entrada)
    assert resultado.estado == "ITERACIONES_COMPLETADAS" and len(resultado.iteraciones) == 5
    assert "evidencia_discontinuidad" not in resultado.diagnostico


@pytest.mark.parametrize("expresion,intervalo,codigo", [
    ("1/x", (-1, 1), "SINGULARIDAD_DETECTADA"), ("tan(x)", (1, 2), "SINGULARIDAD_DETECTADA"),
    ("1/(x*x-.25)", (0, 1), "DOMINIO_INVALIDO"), ("1e-200*(x*x+1)", (-1, 1), "SIN_CAMBIO_DE_SIGNO"),
    ("x*tan(x)", (0, 2), "CERO_EVALUADO"), ("x-.125", (0, 1), "CERO_EVALUADO"),
])
def test_preserva_ceros_y_diagnosticos_previos(expresion, intervalo, codigo):
    """Polos identificados, errores puntuales y ceros tienen precedencia sobre una inferencia."""
    resultado = biseccion(EntradaBiseccion(expresion, *intervalo, 4))
    assert resultado.codigo_diagnostico == codigo
    assert "evidencia_discontinuidad" not in resultado.diagnostico
