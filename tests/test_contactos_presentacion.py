"""Evidencia visible, aptitud y selección explícita de candidatos refinados."""
import json

import pytest
from nicegui import ui

from src.backend.resolutores.raices import contactos_eje
from src.frontend.controladores.biseccion.exploracion import (
    detalles_contacto, presentar_candidato, resolver_exploracion, texto_consumo_exploracion,
)
from tests.comun_biseccion_criterios import ejecutar_escenario
from tests.comun_exploracion_biseccion import acciones_exploracion, activar_accion, preparar_exploracion


@pytest.mark.parametrize("unidad", ["radianes", "grados"])
def test_adaptador_transmite_evidencia_completa(unidad):
    """La presentación muestra cifras del dominio y separa malla de auxiliares en ambas unidades."""
    respuesta = resolver_exploracion({"expresion": "sin(x-.1)**2", "x_min": -1,
                                     "x_max": 1, "paso": .5, "unidad_angular": unidad})
    candidato = respuesta["candidatos"][0]
    assert not presentar_candidato(candidato)["seleccionable"]
    assert respuesta["evaluaciones"] == 5 and respuesta["evaluaciones_refinamiento"] == 24
    assert "Auxiliares: 24/512" in texto_consumo_exploracion(respuesta)
    assert "12 pasos y 24 evaluaciones" in detalles_contacto(candidato)[0]
    assert "sin certificar" in detalles_contacto(candidato)[-1]
    json.dumps(respuesta, allow_nan=False)


def test_registros_anteriores_sin_evidencia_se_siguen_presentando():
    """Una respuesta antigua no requiere campos auxiliares ni los inventa como trabajo ejecutado."""
    assert detalles_contacto({"tipo": "posible_contacto"}) == ()
    texto = texto_consumo_exploracion({"evaluaciones": 3, "candidatos": ()})
    assert "Evaluaciones de malla: 3" in texto and "Auxiliares: 0/512" in texto


def test_contacto_no_certificado_sin_acciones_y_con_evidencia(monkeypatch):
    """La lista real muestra evidencia de un posible contacto y no ofrece cargarlo ni resolverlo."""
    async def comprobar(vista):
        """Explora desde controles existentes y contrasta las etiquetas con el registro vigente."""
        panel = preparar_exploracion(vista, "(x-.1)**2", ".5")
        await panel.explorar()
        candidato = panel.respuesta["candidatos"][0]
        textos = [elemento.text for elemento in panel.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert acciones_exploracion(panel) == [] and not vista.resolucion_multiple.candidatos
        assert all(detalle in textos for detalle in detalles_contacto(candidato))
        assert candidato["mensaje"] in textos and "no certifica" in candidato["mensaje"]
    ejecutar_escenario(monkeypatch, comprobar)


def test_cero_refinado_cargado_exige_calculo_posterior(monkeypatch):
    """La exploración conserva el cálculo previo hasta cargar el nuevo intervalo explícitamente."""
    async def comprobar(vista):
        """Descubre el cero 0.125, conserva estado y luego activa el botón real de selección."""
        panel = preparar_exploracion(vista, "(x-.125)**2", ".5")
        vista.inferior.set_value(".125")
        await vista.resolver()
        previo = vista.ultimo_resultado
        historial = len(vista.historial)
        await panel.explorar()
        candidato = panel.respuesta["candidatos"][0]
        assert candidato["tipo"] == "cero_evaluado" and candidato["abscisa"] == .125
        assert vista.ultimo_resultado is previo and len(vista.historial) == historial
        assert len(acciones_exploracion(panel)) == 1
        activar_accion(acciones_exploracion(panel)[0])
        assert vista.ultimo_resultado is None and vista.obtener_contexto_ia().resultado is None
        assert len(vista.historial) == historial
        assert (float(vista.inferior.value), float(vista.superior.value)) == candidato["intervalo"]
    ejecutar_escenario(monkeypatch, comprobar)


def test_presupuesto_agotado_visible_sin_ocultar_contacto(monkeypatch):
    """Una semilla sin sondeos permanece visible con motivo y advertencia de agotamiento."""
    monkeypatch.setattr(contactos_eje, "MAXIMO_EVALUACIONES_REFINAMIENTO", 0)
    async def comprobar(vista):
        """Muestra la respuesta vigente completa incluso sin presupuesto auxiliar."""
        panel = preparar_exploracion(vista, "(x-.1)**2", ".5")
        await panel.explorar()
        respuesta = panel.respuesta
        textos = [elemento.text for elemento in panel.contenedor_resultados.descendants() if isinstance(elemento, ui.label)]
        assert respuesta["refinamiento_agotado"] and len(respuesta["candidatos"]) == 1
        assert respuesta["advertencias"][-1] in textos
        assert detalles_contacto(respuesta["candidatos"][0])[-1] in textos
        assert acciones_exploracion(panel) == []
    ejecutar_escenario(monkeypatch, comprobar)


def test_cruces_refinados_aptos_para_lote_sin_resolver_automaticamente(monkeypatch):
    """Los signos nuevos habilitan el lote, que solo se ejecuta al pedirlo."""
    async def comprobar(vista):
        """Explora un valle con dos cambios de signo y resuelve ambos por separado."""
        panel = preparar_exploracion(vista, "(x-.125)**2-.001", ".5")
        await panel.explorar()
        lote = vista.resolucion_multiple
        assert all(candidato["tipo"] == "cruce" for candidato in panel.respuesta["candidatos"])
        assert lote.respuesta is None and len(lote.candidatos) == len(acciones_exploracion(panel)) == 2
        await lote.resolver_todos()
        assert len(lote.respuesta["resultados"]) == 2
        assert all(registro["respuesta"]["estado"] == "EXITO" for registro in lote.respuesta["resultados"])
        assert vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)
