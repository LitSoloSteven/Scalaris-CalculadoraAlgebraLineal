"""Política previa y efectiva de continuidad y aislamiento del presupuesto."""
from importlib import import_module

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.contrato_exploracion import CandidatoExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.diagnostico_biseccion import analizar_continuidad_intervalo
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.backend.resolutores.raices.limites_resolucion_multiple import EVALUACIONES_AUXILIARES_CANDIDATO
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos


@pytest.mark.parametrize("expresion,par,unidad,estado,politica,codigo,abscisa", [
    ("x²-2", (2, 1), "radianes", "CONFIRMADA", "PERMITIR", "CONTINUIDAD_ESTRUCTURAL_CONFIRMADA", None),
    ("1/x", (-1, 1), "radianes", "RESTRICCION_DETECTADA", "RECHAZAR", "SINGULARIDAD_DETECTADA", None),
    ("tan(x)", (80, 100), "grados", "RESTRICCION_DETECTADA", "RECHAZAR", "SINGULARIDAD_DETECTADA", None),
    ("tan(x)", (1, 2), "radianes", "RESTRICCION_DETECTADA", "RECHAZAR", "SINGULARIDAD_DETECTADA", None),
    ("sqrt(x)", (-1, 1), "radianes", "RESTRICCION_DETECTADA", "RECHAZAR", "DOMINIO_INVALIDO", -1),
    ("log(x)", (0, 2), "radianes", "RESTRICCION_DETECTADA", "RECHAZAR", "DOMINIO_INVALIDO", 0),
    ("sqrt(x²)-.5", (0, 1), "radianes", "NO_VERIFICADA", "ADVERTIR", "COBERTURA_INSUFICIENTE", None),
    ("sqrt(x)", (0, 1), "radianes", "NO_VERIFICADA", "ADVERTIR", "COBERTURA_INSUFICIENTE", None),
    ("(x-1)/(x-2)", (1, 3), "radianes", "RESTRICCION_DETECTADA", "ADVERTIR", "SINGULARIDAD_DETECTADA", None),
    ("x^2", (1e200, 2e200), "radianes", "NO_VERIFICADA", "ADVERTIR", "EVALUACION_NO_FINITA", 1e200),
])
def test_politica_antes_y_despues_de_resolver(expresion, par, unidad, estado, politica, codigo, abscisa):
    """Comprueba cobertura explícita, polos, extremos, incertidumbre y la excepción local."""
    informe = analizar_continuidad_intervalo(expresion, par, unidad_angular=unidad)
    resultado = biseccion(EntradaBiseccion(expresion, *par, 4, unidad_angular=unidad))
    assert resultado.informe_continuidad == informe
    assert (informe["estado"], informe["politica"]) == (estado, politica)
    assert informe["intervalo"] == tuple(sorted(par))
    evidencia = informe["evidencia"][0]
    assert (evidencia["codigo"], evidencia["abscisa"], evidencia["intervalo"]) == (codigo, abscisa, informe["intervalo"])


@pytest.mark.parametrize("expresion,par,opciones", [
    ("sin(", (0, 1), {}),
    ("x", (1, 1), {}),
    ("x", (1, float("inf")), {}),
    ("x", (1, 2), {"unidad_angular": "vueltas"}),
    ("x", (1, 2), {"cero_preferido": 3}),
    ("x-1", (1, 2), {"cero_preferido": 2}),
])
def test_consulta_invalida(expresion, par, opciones):
    """Las capturas inválidas conservan el contrato de ValueError."""
    with pytest.raises(ValueError):
        analizar_continuidad_intervalo(expresion, par, **opciones)


def test_sospecha_de_traza_es_evidencia_separada():
    """La sospecha conserva el intervalo de la traza y la advertencia efectiva."""
    expresion = "1/(x*x-.2)"
    resultado = biseccion(EntradaBiseccion(expresion, 0, 1, 4))
    informe = resultado.informe_continuidad
    assert informe["estado"] == "NO_VERIFICADA" and informe["politica"] == "ADVERTIR"
    assert informe["evidencia"][-1]["tipo"] == "SOSPECHA_TRAZA"
    assert informe["evidencia"][-1]["intervalo"] == resultado.diagnostico["evidencia_discontinuidad"]["intervalo"]


def test_fallo_interior_actualiza_politica_efectiva():
    """Un fallo observado en el interior se publica con su abscisa y código."""
    resultado = biseccion(EntradaBiseccion("x*sqrt(x*x-.25)", -1, 1, 4))
    informe = resultado.informe_continuidad
    assert (informe["estado"], informe["politica"]) == ("RESTRICCION_DETECTADA", "RECHAZAR")
    evidencia = informe["evidencia"][-1]
    assert (evidencia["tipo"], evidencia["codigo"], evidencia["abscisa"]) == ("FALLO_INTERIOR", "DOMINIO_INVALIDO", 0)


def test_lote_reutiliza_extremos_y_omite_pendiente(monkeypatch):
    """La aptitud y el cálculo comparten evaluaciones por registro dentro de su reserva."""
    modulo = import_module("src.backend.resolutores.raices.resolucion_multiple")
    abscisas = []

    def _compilar_con_contador(expresion):
        funcion = compilar(expresion)

        def _evaluar(valor):
            abscisas.append(valor)
            return funcion(valor)

        return _evaluar

    monkeypatch.setattr(modulo, "compilar", _compilar_con_contador)
    configuracion = EntradaBiseccion("(x-1)/(x-2)", 0, 1, 4, limite_iteraciones=3)
    candidatos = (
        CandidatoResolucion("continuo", CandidatoExploracion("cero_evaluado", (0, 1), 1, 0)),
        CandidatoResolucion("polo", CandidatoExploracion("cero_evaluado", (1, 3), 1, 0)),
        CandidatoResolucion("rechazado", CandidatoExploracion("cruce", (2, 4))),
        CandidatoResolucion("pendiente", CandidatoExploracion("cruce", (5, 6))),
    )
    reserva = configuracion.limite_iteraciones + EVALUACIONES_AUXILIARES_CANDIDATO
    lote = resolver_candidatos(EntradaResolucionMultiple(configuracion, candidatos, reserva * 3))
    assert abscisas == [0, 1, 1, 3, 2, 4]
    primero, segundo, tercero, cuarto = lote.resultados
    assert primero.informe_continuidad["estado"] == "NO_VERIFICADA"
    assert segundo.informe_continuidad["politica"] == "ADVERTIR"
    assert tercero.estado == "NO_APTO" and tercero.informe_continuidad["politica"] == "RECHAZAR"
    assert cuarto.estado == "PRESUPUESTO_AGOTADO" and cuarto.informe_continuidad is None
