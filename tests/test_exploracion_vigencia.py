"""Carreras del trabajador, cancelación, reemplazo del contenedor y reconexión."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_biseccion_criterios import ejecutar_escenario
from tests.comun_exploracion_biseccion import preparar_exploracion


@pytest.mark.parametrize("cambio", ["funcion", "restaurar", "rango", "paso", "criterio", "limpiar", "desconectar"])
def test_edicion_cancela_y_descarta_trabajador_antiguo(monkeypatch, cambio):
    """Incluso si un trabajador termina después de cancelar, no publica sus candidatos."""
    async def comprobar(vista):
        """Retiene la respuesta hasta editar y comprueba descarte por revisión y captura."""
        panel = preparar_exploracion(vista)
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Retiene una respuesta hasta liberarla incluso si su espera fue cancelada."""
            inicio.set()
            try:
                await liberar.wait()
            except asyncio.CancelledError:
                await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(panel.explorar())
        await inicio.wait()
        assert not panel.boton.enabled and panel.tarea is tarea
        _cambiar(vista, cambio)
        liberar.set()
        await tarea
        if cambio == "criterio":
            assert panel.respuesta["estado"] == "EXITO" and panel.respuesta["candidatos"]
            assert panel.boton.enabled and panel.tarea is None
            return
        assert panel.respuesta is None and not list(panel.contenedor_resultados.descendants())
        assert panel.boton.enabled and panel.tarea is None
        assert "disponible" not in panel.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def _cambiar(vista, cambio):
    if cambio in ("funcion", "restaurar"):
        vista.expresion.set_value("x^2-4")
        if cambio == "restaurar":
            vista.expresion.set_value("x^2-1")
    elif cambio == "rango":
        vista.exploracion.minimo.set_value("-3")
    elif cambio == "paso":
        vista.exploracion.paso.set_value(".25")
    elif cambio == "criterio":
        vista.criterio.set_value("ancho")
    elif cambio == "limpiar":
        vista.limpiar_todo()
    else:
        vista._desconectar()


def test_respuesta_antigua_no_sustituye_solicitud_nueva(monkeypatch):
    """El finally del trabajo viejo tampoco libera o altera el estado de otra solicitud."""
    async def comprobar(vista):
        """Resuelve la segunda solicitud antes de permitir que termine la primera."""
        panel = preparar_exploracion(vista)
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Retrasa solo la primera malla para invertir el orden de sus respuestas."""
            if captura["paso"] == ".5":
                inicio.set()
                try:
                    await liberar.wait()
                except asyncio.CancelledError:
                    await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        antigua = asyncio.create_task(panel.explorar())
        await inicio.wait()
        panel.paso.set_value(".25")
        await panel.explorar()
        respuesta = panel.respuesta
        assert respuesta["evaluaciones"] == 17
        liberar.set()
        await antigua
        assert panel.respuesta is respuesta
        assert panel.boton.enabled and panel.tarea is None
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["eliminar", "sustituir", "fallo_obsoleto"])
def test_contenedor_o_error_obsoleto_no_publica(monkeypatch, cambio):
    """Cambiar de contenedor o fallar después de editar no entrega resultados ni errores viejos."""
    async def comprobar(vista):
        """Cambia el destino desde el trabajador simulado sin modificar el servicio de dominio."""
        panel = preparar_exploracion(vista)
        async def trabajar(calcular, captura):
            """Sustituye el destino o falla después de invalidar la captura original."""
            if cambio == "eliminar":
                panel.contenedor_resultados.delete()
            elif cambio == "sustituir":
                with vista.contenedor_resultados:
                    panel.contenedor_resultados = ui.column()
            else:
                panel.paso.set_value(".25")
                raise RuntimeError("fallo antiguo")
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(panel.explorar())
        resultado = await asyncio.gather(tarea, return_exceptions=True)
        if cambio == "fallo_obsoleto":
            assert isinstance(resultado[0], asyncio.CancelledError)
        else:
            assert resultado == [None]
        assert panel.respuesta is None
        assert "No se pudo" not in panel.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def test_desconexion_bloquea_hasta_reconectar(monkeypatch):
    """Reconectar permite explorar de nuevo sin recuperar respuestas o acciones anteriores."""
    async def comprobar(vista):
        """Reproduce los callbacks registrados de desconexión y reconexión."""
        panel = preparar_exploracion(vista)
        await panel.explorar()
        anterior = panel.respuesta
        vista._desconectar()
        await panel.explorar()
        assert panel.respuesta is None
        panel.reabrir()
        await panel.explorar()
        assert panel.respuesta is not anterior and panel.respuesta["estado"] == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)
