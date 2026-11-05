"""Paridad de notación ampliada entre motor, adaptadores, muestreo y lotes."""
import json
from dataclasses import asdict, replace

import pytest

from src.backend.excepciones import ErrorDominio
from src.backend.resolutores.raices.biseccion import biseccion
from src.backend.resolutores.raices.contrato_biseccion import EntradaBiseccion
from src.backend.resolutores.raices.contrato_exploracion import EntradaExploracion
from src.backend.resolutores.raices.contrato_resolucion_multiple import CandidatoResolucion, EntradaResolucionMultiple
from src.backend.resolutores.raices.dominio_intervalo import comprobar_dominio_intervalo
from src.backend.resolutores.raices.exploracion_intervalos import explorar_intervalos
from src.backend.resolutores.raices.normalizacion_funcion import normalizar_expresion
from src.backend.resolutores.raices.resolucion_multiple import resolver_candidatos
from src.frontend.controladores.biseccion.controlador import calcular_presentacion, resolver_captura
from src.frontend.controladores.biseccion.exploracion import resolver_exploracion
from src.frontend.controladores.biseccion.resolucion_multiple import resolver_lote
from src.frontend.controladores.biseccion.vista_previa import preparar_vista_previa
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


@pytest.mark.parametrize("expresion, explicita", [
    ("x²−2", "x**2-2"), ("2x−3", "2*x-3"), ("2(x−1.3)", "2*(x-1.3)"),
    ("(x+1)(x−1.3)", "(x+1)*(x-1.3)"), ("3sin(x)−2.6", "3*sin(x)-2.6"),
    ("ln(x)−.4", "log(x)-.4"), ("log10(x)−.2", "log10(x)-.2"),
    ("log2(x)−.4", "log2(x)-.4"), ("sinh(x)−2", "sinh(x)-2"),
    ("asin(.5x)−.8", "asin(.5*x)-.8"), ("acos(.5x)−.6", "acos(.5*x)-.6"),
    ("atan(x)−.9", "atan(x)-.9"), ("cosh(x)−2", "cosh(x)-2"), ("tanh(x)−.8", "tanh(x)-.8"),
])
def test_motor_presentacion_y_grafica_comparten_sintaxis(expresion, explicita):
    """Notaciones equivalentes producen la misma traza y las mismas 401 muestras finitas."""
    entrada = EntradaBiseccion(expresion, 1, 2, 4)
    resultado = biseccion(entrada)
    assert resultado == biseccion(replace(entrada, expresion=explicita))
    assert resultado.estado == "EXITO"
    captura = {**captura_criterio(), "expresion": expresion}
    respuesta = calcular_presentacion(captura)
    previa = preparar_vista_previa({"expresion": expresion, "x_min": 1, "x_max": 2})
    assert respuesta["iteraciones"] == asdict(resultado)["iteraciones"]
    assert previa["muestra"] == respuesta["muestra"]
    assert len(previa["muestra"]["x"]) == 401
    assert respuesta["entrada"]["expresion"] == expresion
    assert previa["entrada"]["expresion"] == normalizar_expresion(expresion)
    json.dumps((respuesta, previa), allow_nan=False)


def test_exploracion_y_lote_de_notacion_implicita():
    """El escaneo y los lotes conservan dos candidatos y paridad con el motor individual."""
    expresion = "(x+1)(x−1)"
    exploracion = explorar_intervalos(EntradaExploracion(expresion, -2, 2, .3))
    referencia = explorar_intervalos(EntradaExploracion("(x+1)*(x-1)", -2, 2, .3))
    assert exploracion == referencia
    candidatos = tuple(CandidatoResolucion(str(indice), candidato)
                       for indice, candidato in enumerate(exploracion.candidatos) if candidato.tipo == "cruce")
    assert len(candidatos) == 2
    entrada = EntradaResolucionMultiple(EntradaBiseccion(expresion, -2, 2, 4), candidatos)
    lote = resolver_candidatos(entrada)
    assert [registro.resultado.aproximacion for registro in lote.resultados] == pytest.approx([-1, 1], abs=1e-4)
    assert all(registro.resultado == biseccion(registro.entrada) for registro in lote.resultados)
    respuesta = resolver_exploracion({"expresion": expresion, "x_min": -2, "x_max": 2, "paso": .3})
    assert respuesta["candidatos"] == asdict(exploracion)["candidatos"]
    serializada = resolver_lote({"configuracion": {**captura_criterio(), "expresion": expresion},
                               "candidatos": [asdict(candidato) for candidato in candidatos]})
    assert serializada["estado"] == "LOTE_COMPLETADO"
    assert all(registro["respuesta"]["entrada"]["expresion"] == expresion for registro in serializada["resultados"])
    json.dumps((respuesta, serializada), allow_nan=False)


def test_dominio_estructural_consume_notacion_normalizada():
    """El denominador implícito conserva su polo aun sin evaluar exactamente su cero."""
    expresion = "1/(2x−.1234)"
    with pytest.raises(ErrorDominio) as fallo:
        comprobar_dominio_intervalo(expresion, (-1, 1))
    assert fallo.value.codigo == "SINGULARIDAD_DETECTADA"
    resultado = biseccion(EntradaBiseccion(expresion, -1, 1, 4))
    assert resultado.estado == "ERROR" and resultado.codigo_diagnostico == "SINGULARIDAD_DETECTADA"
    previa = preparar_vista_previa({"expresion": "1/x²", "x_min": -1, "x_max": 1})
    assert previa["estado"] == "EXITO" and previa["muestra"]["y"][200] is None


@pytest.mark.parametrize("expresion", ["__import__('os')", "x.real", "sinx", "(-8)^(1/3)"])
def test_fallos_serializables_en_adaptadores(expresion):
    """Una entrada inválida entrega error o muestras huecas sin exponer valores no finitos."""
    respuesta = resolver_captura({**captura_criterio(), "expresion": expresion})
    assert respuesta["estado"] == "ERROR" and respuesta.get("aproximacion") is None
    previa = preparar_vista_previa({"expresion": expresion, "x_min": 1, "x_max": 2})
    assert previa["estado"] == "ERROR" or all(valor is None for valor in previa["muestra"]["y"])
    json.dumps((respuesta, previa), allow_nan=False)


def test_captura_historial_y_contexto_conservan_notacion(monkeypatch):
    """El formulario restaura el texto matemático y una edición invalida su resultado vigente."""
    async def comprobar(vista):
        """Resuelve con los callbacks reales y restaura la captura sin recalcular."""
        vista.cargar_captura({**captura_criterio(), "expresion": "x²−2"})
        await vista.resolver()
        assert vista.ultimo_resultado["estado"] == "EXITO"
        assert vista.historial[0]["captura"]["expresion"] == "x²−2"
        assert vista.obtener_contexto_ia().entrada["expresion"] == "x²−2"
        vista.cargar_captura(vista.historial[0]["captura"])
        assert vista.expresion.value == "x²−2" and vista.ultimo_resultado is None
        await vista.resolver()
        vista.expresion.set_value("2x−3")
        assert vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)
