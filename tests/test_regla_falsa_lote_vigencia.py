"""Vigencia del lote ante ediciones, búsquedas nuevas y pérdida de conexión."""
import asyncio

import pytest
from nicegui import run, ui

from src.frontend.vistas.regla_falsa.modos_captura import MODO_INTERVALO
from tests.comun_regla_falsa_vista import ejecutar_escenario
from tests.test_regla_falsa_lote_interfaz import preparar_lote_vista


@pytest.mark.parametrize("cambio", ["expresion", "unidad", "rango", "criterio", "seleccion", "modo", "conexion"])
def test_lote_pendiente_descarta_captura_revocada(monkeypatch, cambio):
    """Impide publicar la respuesta anterior aunque se restablezcan los valores de captura."""
    async def comprobar(vista):
        """Retiene el trabajador, cambia la captura y libera su respuesta real."""
        panel = await preparar_lote_vista(vista)
        panel.selector.set_value(list(panel.candidatos))
        inicio, liberar = asyncio.Event(), asyncio.Event()

        async def trabajar(calcular, captura):
            """Retiene la plaza real hasta que termine el cambio de captura."""
            inicio.set()
            await liberar.wait()
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(panel.resolver())
        await asyncio.wait_for(inicio.wait(), 2)
        _revocar(vista, panel, cambio)
        assert panel.coordinador.activos == 1 and panel.tarea is None
        liberar.set()
        await asyncio.wait_for(tarea, 2)
        await asyncio.wait_for(panel.coordinador.esperar_cierre(), 2)
        assert panel.respuesta is None and panel.activo is None and vista.ultimo_resultado is None
        assert not list(panel.contenedor_resultados)
    ejecutar_escenario(monkeypatch, comprobar)


def _revocar(vista, panel, cambio):
    if cambio == "conexion":
        vista.cerrar()
        vista.reabrir()
        return
    campo, valor = {"expresion": (vista.expresion, "x"), "unidad": (vista.unidad_angular, "grados"),
                    "rango": (vista.exploracion.minimo, "-1"), "criterio": (vista.criterio, "ancho"),
                    "seleccion": (panel.selector, []), "modo": (vista.modos, MODO_INTERVALO)}[cambio]
    previo = campo.value
    campo.set_value(valor)
    campo.set_value(previo)


def test_boton_obsoleto_no_abre_detalle_de_un_lote_nuevo(monkeypatch):
    """Una acción de un lote anterior no reutiliza su identificador en la publicación nueva."""
    async def comprobar(vista):
        """Resuelve dos veces la misma selección y simula el click tardío de la primera."""
        panel = await preparar_lote_vista(vista)
        panel.selector.set_value([next(iter(panel.candidatos))])
        await panel.resolver()
        viejo = next(elemento for elemento in panel.contenedor_resultados.descendants() if isinstance(elemento, ui.button))
        manejador = next(evento.handler for evento in viejo._event_listeners.values() if evento.type == "click")
        await panel.resolver()
        assert viejo.is_deleted
        manejador(None)
        assert panel.activo is None and vista.ultimo_resultado is None
        panel.abrir(panel.respuesta["resultados"][0]["identificador"], panel.respuesta)
        assert vista.ultimo_resultado is not None
        vista.exploracion.minimo.set_value("-2")
        assert panel.activo is None and vista.obtener_contexto_ia().foco is None
    ejecutar_escenario(monkeypatch, comprobar)
