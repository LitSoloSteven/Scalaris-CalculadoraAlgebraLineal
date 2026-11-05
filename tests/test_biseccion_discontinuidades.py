"""Sospechas sustentadas por filas válidas y prioridad de los fallos observados."""
from dataclasses import replace
from importlib import import_module

import pytest

from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.criterios_biseccion import CriterioParada
from src.backend.resolutores.raices.evaluador_funcion import compilar
from src.frontend.controladores.biseccion.controlador import serializar_resultado


@pytest.mark.parametrize("expresion,intervalo,unidad", [
    ("1/(x*x-.2)", (0, 1), "radianes"), ("tan(x*x)", (1, 1.5), "radianes"),
    ("tan(x*x)", (9, 10), "grados"), ("1e-308/(x*x-.2)", (0, 1), "radianes"),
    ("1e302/(x*x-.2)", (0, 1), "radianes"),
])
def test_sospecha_conserva_traza_y_cierre_sin_afirmar_raiz(expresion, intervalo, unidad):
    """La contracción y el crecimiento relativo califican el mismo punto medio y criterio."""
    resultado = biseccion(EntradaBiseccion(expresion, *intervalo, 4, unidad_angular=unidad))
    assert resultado.estado == "CONTINUIDAD_NO_VERIFICADA"
    assert resultado.codigo_diagnostico == "DISCONTINUIDAD_SOSPECHADA"
    assert resultado.motivo_parada == "ancho_menor_que_E" and resultado.contexto_fallo is None
    ultima = resultado.iteraciones[-1]
    evidencia = resultado.diagnostico["evidencia_discontinuidad"]
    assert resultado.diagnostico["origen"] == "traza"
    assert resultado.aproximacion == ultima.c and resultado.metrica_final == ultima.ancho
    assert resultado.intervalo_final == evidencia["intervalo"]
    assert evidencia["magnitud_vecinal_final"] == min(abs(ultima.f_a), abs(ultima.f_b))
    assert evidencia["residuo_reciente_minimo"] == min(fila.residuo for fila in resultado.iteraciones[-3:])
    assert evidencia["ancho_referencia"] >= 16 * ultima.ancho
    assert resultado.unidad_angular == unidad


@pytest.mark.parametrize("criterio,motivo", [
    (CriterioParada("iteraciones", 15), "iteraciones_completadas"),
    (CriterioParada("relativo", .001), "relativo_menor_que_porcentaje"),
    (CriterioParada("residuo", .1), "limite_iteraciones"),
])
def test_sospecha_no_escoge_otro_criterio(criterio, motivo):
    """La advertencia coexiste con la condición efectiva y el mismo criterio solicitado."""
    resultado = biseccion(EntradaBiseccion("1/(x*x-.2)", 0, 1, 4, 30, criterio=criterio))
    assert resultado.estado == "CONTINUIDAD_NO_VERIFICADA" and resultado.motivo_parada == motivo
    assert resultado.criterio_solicitado == criterio and resultado.diagnostico["mensaje_parada"]


def test_fallo_observado_conserva_codigo_y_abscisa_con_evidencia_adicional():
    """Un polo alcanzado conserva el error y adjunta el crecimiento de las filas previas."""
    punto = 819 / 4096
    resultado = biseccion(EntradaBiseccion(f"1/(x*x-{punto*punto!r})", 0, 1, 15))
    assert resultado.estado == "ERROR" and resultado.codigo_diagnostico == "DOMINIO_INVALIDO"
    assert resultado.aproximacion is None and len(resultado.iteraciones) == 11
    assert resultado.contexto_fallo["x_fallo"] == punto and resultado.contexto_fallo["etapa"] == "iteracion"
    assert resultado.diagnostico["origen"] == "iteracion" and resultado.diagnostico["evidencia_discontinuidad"]
    assert any("sugiere una discontinuidad" in aviso for aviso in resultado.advertencias)


def test_presupuesto_nulo_de_evaluaciones_adicionales(monkeypatch):
    """La inferencia reutiliza los dos extremos y las evaluaciones de cada fila."""
    modulo = import_module("src.backend.resolutores.raices.biseccion")
    llamadas = []
    def compilar_contada(expresion):
        """Envuelve el evaluador real con un contador sin alterar sus valores."""
        funcion = compilar(expresion)
        def evaluar_contada(abscisa):
            """Cuenta cada evaluación solicitada por el motor."""
            llamadas.append(abscisa)
            return funcion(abscisa)
        return evaluar_contada
    monkeypatch.setattr(modulo, "compilar", compilar_contada)
    resultado = biseccion(EntradaBiseccion("1/(x*x-.2)", 0, 1, 4))
    assert resultado.codigo_diagnostico == "DISCONTINUIDAD_SOSPECHADA"
    assert llamadas == [0, 1, *(fila.c for fila in resultado.iteraciones)]


@pytest.mark.parametrize("cambios", [
    {"iteraciones": ()}, {"motivo_parada": "residuo_menor_que_delta"}, {"motivo_parada": "raiz_exacta"},
])
def test_serializacion_rechaza_cierre_provisional_incoherente(cambios):
    """Un estado provisional conserva la verificación de la fila y del criterio satisfecho."""
    entrada = EntradaBiseccion("1/(x*x-.2)", 0, 1, 4)
    resultado = biseccion(entrada)
    with pytest.raises(ValueError):
        serializar_resultado(entrada, replace(resultado, **cambios))
