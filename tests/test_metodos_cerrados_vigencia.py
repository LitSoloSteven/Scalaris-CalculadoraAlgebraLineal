"""Vigencia de la exploración, la gráfica y las explicaciones del procedimiento."""
import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from nicegui import run, ui

from src.frontend.componentes.modos_captura_raices import MODO_BUSQUEDA, MODO_INTERVALO
from src.frontend.controladores.metodos_cerrados.adaptadores import BISECCION, REGLA_FALSA
from tests.test_metodos_cerrados_calculo import captura_ejercicio, montar_vista


@asynccontextmanager
async def _retener(monkeypatch, coordinador):
    ejecutar = run.io_bound
    inicio, liberar = asyncio.Event(), asyncio.Event()

    async def _trabajador(funcion, captura, *argumentos, **opciones):
        if funcion is coordinador._calcular and captura.get("metodo", BISECCION) == BISECCION:
            inicio.set()
            await liberar.wait()
        return await ejecutar(funcion, captura, *argumentos, **opciones)

    with monkeypatch.context() as cambios:
        cambios.setattr(run, "io_bound", _trabajador)
        try:
            yield inicio
        finally:
            liberar.set()
            await asyncio.wait_for(coordinador.esperar_cierre(), 5)


@pytest.mark.parametrize("operacion", ("buscar", "lote"))
def test_trabajo_tardio_del_otro_metodo_no_reaparece(monkeypatch, operacion):
    """El trabajador revocado puede terminar después de la búsqueda del método activo."""
    async def _comprobar():
        async with montar_vista(monkeypatch) as (vista, _):
            vista.cargar_captura({"expresion": "(x+1)*(x-1)*(x-2)"})
            vista.modos.set_value(MODO_BUSQUEDA)
            exploracion = vista.exploracion
            exploracion.definir_rango((-2.1, 2.9))
            exploracion.paso.set_value("0.25")
            panel, accion = exploracion, exploracion.buscar
            if operacion == "lote":
                await exploracion.buscar()
                panel = exploracion.lote
                accion = lambda: panel._resolver(True, True)
            async with _retener(monkeypatch, panel.coordinador) as inicio:
                anterior = asyncio.create_task(accion())
                await asyncio.wait_for(inicio.wait(), 5)
                vista.captura.metodo.set_value(REGLA_FALSA)
                await asyncio.wait_for(exploracion.buscar(), 5)
                vigente = exploracion.respuesta
                assert vigente["estado"] == "EXITO"
            await anterior
            assert exploracion.respuesta is vigente
            assert exploracion.lote.respuesta is None and vista.candidato_activo is None
            assert panel.tarea is None
    asyncio.run(_comprobar())


def test_muestra_pendiente_no_redibuja_tras_cerrar(monkeypatch):
    """La última respuesta del trabajador no actualiza el nodo de un cliente cerrado."""
    async def _comprobar():
        async with montar_vista(monkeypatch) as (vista, _):
            grafica = vista.grafica
            async with _retener(monkeypatch, grafica.coordinador) as inicio:
                vista.cargar_captura({"expresion": "x^2 - 2"})
                await asyncio.wait_for(inicio.wait(), 5)
                vista.cerrar()
                figura = grafica.nodo.figure
            assert grafica.nodo.figure is figura
            assert grafica.previa is None
    asyncio.run(_comprobar())


def test_marca_antigua_se_ignora_y_el_borrador_se_puede_confirmar(monkeypatch):
    """Alterna el método con la misma curva y valida la identidad de los clics."""
    async def _comprobar():
        async with montar_vista(monkeypatch) as (vista, _):
            vista.cargar_captura(captura_ejercicio("x", "-2", "2", "radianes"))
            await vista.grafica.tarea
            curva = vista.grafica.nodo.figure.data[0]
            punto = {"curveNumber": 0, "pointIndex": 1, "x": curva.x[1], "y": curva.y[1],
                     "customdata": curva.customdata[1]}
            evento = SimpleNamespace(args={"points": [punto]})
            seleccion = vista.grafica.seleccion
            seleccion.iniciar()
            seleccion._marcar(evento)
            assert float(seleccion.campos[0].value) == punto["x"]
            vista.captura.metodo.set_value(REGLA_FALSA)
            assert not seleccion.activa
            vista.modos.set_value(MODO_BUSQUEDA)
            original = vista.exploracion.capturar_rango()
            vista.grafica._encuadrar_busqueda(SimpleNamespace(
                args={"identidad": punto["customdata"], "xaxis.range": [-3, 3]},
            ))
            assert vista.exploracion.capturar_rango() == original
            seleccion.iniciar()
            seleccion._marcar(evento)
            assert seleccion.campos[0].value == ""
            for campo, valor in zip(seleccion.campos, ("-1", "1")):
                campo.set_value(valor)
            seleccion.confirmar()
            assert vista.modos.value == MODO_INTERVALO
            assert (float(vista.inferior.value), float(vista.captura.superior.value)) == (-1, 1)
            assert vista.ultimo_resultado is None
    asyncio.run(_comprobar())


def test_glosa_descarta_la_explicacion_encolada_de_otro_paso(monkeypatch):
    """Un clic que ya estaba encolado se evalúa otra vez antes de enviar."""
    async def _comprobar():
        async with montar_vista(monkeypatch) as (vista, _):
            panel = vista.panel_ia
            consultas, enviadas = [], []

            async def _enviar(*_argumentos, **_opciones):
                enviadas.append(vista.obtener_contexto_ia())

            monkeypatch.setattr(panel, "programar_actualizacion_contexto", lambda: None)
            monkeypatch.setattr(panel, "_lanzar_tarea", consultas.append)
            monkeypatch.setattr(panel, "_enviar_consulta", _enviar)
            vista.cargar_captura(captura_ejercicio("x^2 - 2", "1", "2", "radianes"))
            await vista.resolver()
            reproductor = vista.salida.reproductor
            reproductor.ir_a(1)
            reproductor.al_explicar(reproductor.pasos[1])
            reproductor.ir_a(2)
            await consultas.pop()
            assert not enviadas and panel.foco_explicacion is None
            reproductor.al_explicar(reproductor.pasos[2])
            await consultas.pop()
            assert enviadas[0].herramienta == BISECCION and enviadas[0].foco.indice == 3
            reproductor.al_explicar(reproductor.pasos[2])
            vista.captura.metodo.set_value(REGLA_FALSA)
            await consultas.pop()
            assert len(enviadas) == 1 and panel.foco_explicacion is None
    asyncio.run(_comprobar())


@pytest.mark.parametrize("metodo", (BISECCION, REGLA_FALSA))
def test_diagnostico_de_dominio_carga_intervalo_sin_resolver(monkeypatch, metodo):
    """Ejecuta la acción de la propuesta y conserva su asociación con el resultado."""
    async def _comprobar():
        async with montar_vista(monkeypatch, metodo) as (vista, _):
            vista.cargar_captura(captura_ejercicio("sqrt(x)-1", "-1", "4", "radianes"))
            await vista.resolver()
            boton = next(elemento for elemento in vista.contenedor_resultados.descendants()
                         if isinstance(elemento, ui.button) and elemento.text == "Cargar intervalo [0, 4]")
            accion = next(evento.handler for evento in boton._event_listeners.values() if evento.type == "click")
            accion(None)
            assert (float(vista.inferior.value), float(vista.captura.superior.value)) == (0, 4)
            assert vista.ultimo_resultado is None
            assert vista.obtener_contexto_ia().resultado is None
    asyncio.run(_comprobar())
