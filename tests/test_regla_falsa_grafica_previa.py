"""Previa independiente, rango compartido y descarte de muestreos antiguos."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from nicegui import run

from src.frontend.controladores.vista_previa_raices import preparar_vista_previa
from tests.comun_regla_falsa_vista import captura_regla_falsa, ejecutar_escenario


@pytest.mark.parametrize("expresion", ["x^2-2", "sqrt(x)-1", "1/(x-0.1234)", "2sin(x)-1"])
def test_previa_sin_extremos_ni_parada(monkeypatch, expresion):
    """El campo real genera muestras finitas sin solver ni historial."""
    async def comprobar(vista):
        """Espera la solicitud automática y verifica el nodo nativo estable."""
        panel = vista.vista_previa
        nodo = panel.grafica
        vista.tolerancia.set_value("inválida")
        vista.limite.set_value("")
        vista.expresion.set_value(expresion)
        await panel.tarea
        assert panel.respuesta["estado"] == "EXITO" and panel.grafica is nodo
        assert vista.inferior.value == vista.superior.value == ""
        assert vista.ultimo_resultado is None and not vista.historial
        figura = panel.grafica.figure
        assert figura["layout"]["hovermode"] == "closest"
        assert figura["data"][0]["hoverinfo"] == "none"
        assert figura["data"][0]["connectgaps"] is False
        assert figura["data"][1]["meta"]["scalaris_colores"]["marker.color"] == "serie:1"
        if expresion.startswith(("sqrt", "1/")):
            assert panel.respuesta["muestra"]["huecos"]
        json.dumps(panel.respuesta, allow_nan=False)
    ejecutar_escenario(monkeypatch, comprobar)


def test_rango_sincronizado_conserva_el_resultado(monkeypatch):
    """Editar rango gráfico o exploratorio no invalida el cálculo individual."""
    async def comprobar(vista):
        """Compara identidad del resultado y captura matemática tras sincronizar límites."""
        vista.cargar_captura(captura_regla_falsa())
        await vista.resolver()
        resultado, captura = vista.ultimo_resultado, vista.capturar()
        panel = vista.vista_previa
        panel.minimo.set_value("-3")
        panel.maximo.set_value("3")
        await panel.tarea
        assert vista.exploracion.minimo.value == "-3" and vista.exploracion.maximo.value == "3"
        vista.exploracion.minimo.set_value("-4")
        await panel.tarea
        assert panel.minimo.value == "-4"
        assert vista.ultimo_resultado is resultado and vista.capturar() == captura
        assert len(vista.historial) == 1
        vista.limpiar_todo()
        assert panel.minimo.value == "-10" and panel.maximo.value == "10"
        assert panel.respuesta is None and panel.tarea is None
    ejecutar_escenario(monkeypatch, comprobar)


def test_rafaga_y_reconexion_descartan_trabajo_antiguo(monkeypatch):
    """Cincuenta capturas conservan una plaza y un borrador; el cierre revoca ambos destinos."""
    async def comprobar(vista):
        """Retiene el trabajador real con eventos, sin esperas temporizadas de concurrencia."""
        inicio, liberar = asyncio.Event(), asyncio.Event()
        capturas = []
        async def trabajar(calcular, captura):
            """Retiene el cálculo hasta que la prueba libera explícitamente su plaza."""
            capturas.append(captura)
            inicio.set()
            await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        panel = vista.vista_previa
        vista.expresion.set_value("x-1")
        primera = asyncio.create_task(panel.actualizar())
        await inicio.wait()
        for indice in range(2, 52):
            vista.expresion.set_value(f"x-{indice}")
            ultima = asyncio.create_task(panel.actualizar())
            await asyncio.sleep(0)
            assert panel.coordinador.activos == panel.coordinador.pendientes == 1
        vista.cerrar()
        await ultima
        liberar.set()
        await primera
        await panel.coordinador.esperar_cierre()
        assert len(capturas) == 1 and panel.respuesta is None
        vista.reabrir()
        await panel.tarea
        assert panel.respuesta["entrada"]["expresion"] == "x-51"
        assert panel.coordinador.activos == panel.coordinador.pendientes == 0
    ejecutar_escenario(monkeypatch, comprobar)


def test_unidades_y_limites_reutilizan_el_dominio():
    """Los grados modifican las evaluaciones sin consultar criterios de parada."""
    captura = {"expresion": "sin(x)", "x_min": "0", "x_max": "90"}
    grados = preparar_vista_previa({**captura, "unidad_angular": "grados"})
    radianes = preparar_vista_previa(captura)
    assert grados["muestra"]["y"][-1] == pytest.approx(1)
    assert grados["muestra"]["y"][-1] != radianes["muestra"]["y"][-1]


def test_encuadre_sincroniza_sin_cargar_extremos(monkeypatch):
    """El encuadre nativo valida límites y no convierte el rango visual en intervalo matemático."""
    async def comprobar(vista):
        """Envía zoom y eventos ajenos a límites con la curva ya publicada."""
        panel = vista.vista_previa
        vista.expresion.set_value("x^2-2")
        await panel.tarea
        panel._encuadrar(SimpleNamespace(args={"xaxis.range[0]": -2, "xaxis.range[1]": 3}))
        await panel.tarea
        assert panel.minimo.value == vista.exploracion.minimo.value == "-2.0"
        assert panel.maximo.value == vista.exploracion.maximo.value == "3.0"
        for datos in ({"xaxis.range": [0, float("inf")]}, {"xaxis.range": [2, 1]}, None):
            panel._encuadrar(SimpleNamespace(args=datos))
        assert panel.tarea is None and panel.minimo.value == "-2.0"
        assert vista.inferior.value == vista.superior.value == "" and vista.ultimo_resultado is None
    ejecutar_escenario(monkeypatch, comprobar)
