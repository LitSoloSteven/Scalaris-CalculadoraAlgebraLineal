"""Búsqueda, carga por acción y lotes reales en el cliente simulado."""
import asyncio
from inspect import isawaitable
from types import SimpleNamespace

import pytest
from nicegui import ui

from src.frontend.componentes.modos_captura_raices import MODO_BUSQUEDA, MODO_INTERVALO
from src.frontend.componentes.copia_resultado import texto_resultado_copiable
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from src.frontend.vistas.biseccion import resumen_criterio
from src.frontend.vistas.regla_falsa import resultado as salida_regla_falsa
from tests.test_metodos_cerrados_calculo import captura_ejercicio, montar_vista


async def _buscar(vista, cliente):
    vista.modos.set_value(MODO_BUSQUEDA)
    vista.exploracion.definir_rango(("-2.1", "2.9"))
    vista.exploracion.paso.set_value("0.25")
    formulario = next(elemento for elemento in cliente.elements.values() if elemento.tag == "form")
    await _activar(formulario, "submit.prevent")
    assert vista.exploracion.respuesta["estado"] == "EXITO"
    return vista.exploracion.lote


async def _activar(elemento, tipo="click"):
    manejador = next(evento.handler for evento in elemento._event_listeners.values() if evento.type == tipo)
    anteriores = asyncio.all_tasks()
    resultado = manejador(None) if tipo == "click" else manejador()
    if isawaitable(resultado):
        await resultado
    for salida in await asyncio.gather(*(asyncio.all_tasks() - anteriores), return_exceptions=True):
        if isinstance(salida, Exception):
            raise salida


def _boton(elementos, etiqueta):
    return next(elemento for elemento in elementos
                if isinstance(elemento, ui.button) and elemento.text.startswith(etiqueta))


async def _resolver_lote(lote, metodo):
    if metodo == BISECCION:
        await _activar(lote.boton_todos)
    else:
        opciones = list(lote.selector_multiple.options)
        assert len(opciones) == 3 and not lote.boton_seleccion.enabled
        lote.selector_multiple.set_value(opciones[:2])
        await _activar(lote.boton_seleccion)


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_busqueda_lote_detalle_y_vuelta_comparten_grafica(monkeypatch, metodo):
    """Resuelve el polinomio, abre un registro vigente y restaura cálculo y malla."""
    copias = []
    for modulo in (resumen_criterio, salida_regla_falsa):
        monkeypatch.setattr(modulo, "renderizar_copia_resultado", copias.append)

    async def _comprobar():
        async with montar_vista(monkeypatch, metodo) as (vista, cliente):
            vista.cargar_captura(captura_ejercicio("(x+1)*(x-1)*(x-2)", "0.5", "1.5", "radianes"))
            await vista.resolver()
            resultado = vista.ultimo_resultado
            vista.salida.reproductor.ir_a(1)
            grafica = vista.grafica.nodo
            lote = await _buscar(vista, cliente)
            await _resolver_lote(lote, metodo)
            registros = lote.respuesta["resultados"]
            assert len(registros) == (3 if metodo == BISECCION else 2)
            primer_candidato = registros[0]["identificador"]
            await _activar(_boton(lote.contenedor_resultados.descendants(), f"Abrir {primer_candidato}"))
            assert vista.candidato_activo == primer_candidato and vista.ultimo_resultado is not resultado
            assert vista.obtener_contexto_ia().entrada["identificador_candidato"] == primer_candidato
            assert vista.grafica.nodo is grafica
            assert sum(isinstance(elemento, ui.plotly) for elemento in cliente.elements.values()) == 1
            assert texto_resultado_copiable(copias[-1]()).splitlines()[1] == primer_candidato
            _comprobar_encuadre_detalle(vista, registros)
            await _activar(_boton(lote.contenedor_resultados.descendants(), "Volver al cálculo principal"))
            assert vista.candidato_activo is None and vista.ultimo_resultado is resultado
            assert vista.salida.reproductor.indice_actual == 1
            assert "identificador_candidato" not in vista.obtener_contexto_ia().entrada
            assert vista.grafica.resultado["resultado"] is resultado
            vista.modos.set_value(MODO_INTERVALO)
            vista.modos.set_value(MODO_BUSQUEDA)
            assert lote.respuesta["resultados"] is registros

    asyncio.run(_comprobar())


def _comprobar_encuadre_detalle(vista, registros):
    grafica = vista.grafica
    rango = vista.exploracion.capturar_rango()
    grafica.ajustar_intervalo()
    entrada = vista.ultimo_resultado["entrada"]
    assert tuple(grafica.nodo.figure.layout.xaxis.range) == (entrada["extremo_izquierdo"], entrada["extremo_derecho"])
    grafica._encuadrar_busqueda(SimpleNamespace(args={"identidad": grafica.identidad, "xaxis.range": [-2, 2]}))
    assert vista.exploracion.capturar_rango() == rango
    assert vista.exploracion.lote.respuesta["resultados"] is registros


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_cargar_intervalo_desde_lista_no_resuelve(monkeypatch, metodo):
    """La acción nativa del candidato cambia a captura individual y preserva sus extremos."""
    async def _comprobar():
        async with montar_vista(monkeypatch, metodo) as (vista, cliente):
            vista.cargar_captura(captura_ejercicio("(x+1)*(x-1)*(x-2)", "", "", "radianes"))
            await _buscar(vista, cliente)
            controles = vista.exploracion.contenedor_resultados.descendants()
            await _activar(_boton(controles, "Cargar intervalo"))
            captura = vista.capturar()
            assert float(captura["extremo_izquierdo"]) < -1 < float(captura["extremo_derecho"])
            assert vista.modos.value == MODO_INTERVALO and vista.ultimo_resultado is None

    asyncio.run(_comprobar())


def test_lote_regla_falsa_respeta_presupuesto_y_seleccion(monkeypatch):
    """La reserva insuficiente deja un registro pendiente y conserva el estado del candidato resuelto."""
    async def _comprobar():
        async with montar_vista(monkeypatch, REGLA_FALSA) as (vista, cliente):
            datos = captura_ejercicio("(x+1)*(x-1)*(x-2)", "", "", "radianes")
            vista.cargar_captura({**datos, "limite_iteraciones": "20"})
            lote = await _buscar(vista, cliente)
            lote.selector_multiple.set_value(list(lote.selector_multiple.options)[:2])
            lote.presupuesto.set_value("23")
            await _activar(lote.boton_seleccion)
            assert lote.respuesta["estado"] == "LOTE_PARCIAL"
            assert [registro["estado"] for registro in lote.respuesta["resultados"]] == ["EXITO", "PRESUPUESTO_AGOTADO"]
            assert all(elemento.text != "Abrir candidato-2" for elemento in lote.contenedor_resultados.descendants()
                       if isinstance(elemento, ui.button))

    asyncio.run(_comprobar())
