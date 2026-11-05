"""Carreras, antirrebote y limpieza de la gráfica previa con controles reales."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_biseccion_criterios import ejecutar_escenario


def test_ediciones_rapidas_muestrean_solo_la_ultima_captura(monkeypatch):
    """Sustituir varias esperas antes de su plazo ejecuta un único trabajador."""
    async def comprobar(vista):
        """Cuenta llamadas tras programar funciones y rangos consecutivos sin ceder el bucle."""
        llamadas = []
        async def trabajar(calcular, captura):
            """Registra la captura que logra superar el antirrebote."""
            llamadas.append(captura)
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        panel = vista.vista_previa
        vista.expresion.set_value("x")
        primera = panel.tarea
        vista.expresion.set_value("x^2")
        panel.minimo.set_value("-1")
        panel.maximo.set_value("3")
        await panel.tarea
        assert primera.cancelled() and llamadas == [{"expresion": "x^2", "x_min": "-1", "x_max": "3"}]
        assert panel.respuesta["entrada"]["expresion"] == "x**2"
        assert panel.tarea is None and panel.estado._props["aria-busy"] == "false"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["funcion", "restaurar", "rango", "restaurar_rango", "criterio", "limpiar", "desconectar"])
def test_trabajador_tardio_no_publica_tras_edicion(monkeypatch, cambio):
    """La respuesta se descarta aun si el trabajador ignora una cancelación y termina."""
    async def comprobar(vista):
        """Retiene el servicio hasta invalidar su revisión desde los controles de usuario."""
        vista.expresion.set_value("x")
        panel = vista.vista_previa
        inicio, liberar = asyncio.Event(), asyncio.Event()
        async def trabajar(calcular, captura):
            """Simula un hilo que termina después de la cancelación de su espera."""
            inicio.set()
            try:
                await liberar.wait()
            except asyncio.CancelledError:
                await liberar.wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        tarea = asyncio.create_task(panel.actualizar())
        await inicio.wait()
        assert panel.estado._props["aria-busy"] == "true"
        _cambiar(vista, cambio)
        liberar.set()
        await tarea
        if cambio == "criterio":
            assert panel.respuesta["estado"] == "EXITO"
            assert panel.estado._props["aria-busy"] == "false"
            return
        assert panel.respuesta is None and not list(panel.contenedor_resultados.descendants())
        assert panel.estado._props["aria-busy"] == "false"
        assert "disponible" not in panel.estado.text
    ejecutar_escenario(monkeypatch, comprobar)


def _cambiar(vista, cambio):
    panel = vista.vista_previa
    if cambio in ("funcion", "restaurar"):
        vista.expresion.set_value("x^2")
        if cambio == "restaurar":
            vista.expresion.set_value("x")
    elif cambio in ("rango", "restaurar_rango"):
        panel.minimo.set_value("-3")
        if cambio == "restaurar_rango":
            panel.minimo.set_value("-10")
    elif cambio == "criterio":
        vista.criterio.set_value("ancho")
    elif cambio == "limpiar":
        vista.limpiar_todo()
    else:
        vista._desconectar()


def test_finally_antiguo_no_libera_solicitud_nueva(monkeypatch):
    """Una tarea antigua que termina mientras otra trabaja no habilita su botón ni la reemplaza."""
    async def comprobar(vista):
        """Libera el trabajador cancelado manteniendo retenida la nueva solicitud."""
        vista.expresion.set_value("x")
        panel = vista.vista_previa
        inicios, permisos = [asyncio.Event(), asyncio.Event()], [asyncio.Event(), asyncio.Event()]
        async def trabajar(calcular, captura):
            """Mantiene dos solicitudes pendientes hasta liberar cada respuesta por separado."""
            indice = int(captura["expresion"] != "x")
            inicios[indice].set()
            try:
                await permisos[indice].wait()
            except asyncio.CancelledError:
                await permisos[indice].wait()
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        antigua = asyncio.create_task(panel.actualizar())
        await inicios[0].wait()
        vista.expresion.set_value("x^2")
        nueva = asyncio.create_task(panel.actualizar())
        await inicios[1].wait()
        permisos[0].set()
        await antigua
        assert panel.tarea is nueva and panel.estado._props["aria-busy"] == "true" and panel.respuesta is None
        permisos[1].set()
        await nueva
        assert panel.respuesta["entrada"]["expresion"] == "x**2"
        assert panel.tarea is None and panel.estado._props["aria-busy"] == "false"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["eliminar", "sustituir", "fallo_obsoleto", "fallo_vigente"])
def test_destino_y_errores_del_trabajador(monkeypatch, cambio):
    """Solo un error vigente muestra una guía de reintento; los destinos antiguos no reciben datos."""
    async def comprobar(vista):
        """Cambia el contenedor o falla desde un trabajador simulado sin alterar el muestreo."""
        vista.expresion.set_value("x")
        panel = vista.vista_previa
        async def trabajar(calcular, captura):
            """Provoca pérdida del destino o error para comprobar las guardas de publicación."""
            if cambio == "eliminar":
                panel.contenedor_resultados.delete()
            elif cambio == "sustituir":
                with vista.contenedor_resultados:
                    panel.contenedor_resultados = ui.column()
            elif cambio == "fallo_obsoleto":
                panel.minimo.set_value("-3")
                raise RuntimeError("fallo antiguo")
            else:
                raise RuntimeError("detalle interno que no debe publicarse")
            return calcular(captura)
        monkeypatch.setattr(run, "io_bound", trabajar)
        await asyncio.gather(asyncio.create_task(panel.actualizar()), return_exceptions=True)
        assert panel.respuesta is None
        assert ("No se pudo dibujar" in panel.estado.text) == (cambio == "fallo_vigente")
        assert "detalle interno" not in panel.estado.text and panel.estado._props["aria-busy"] == "false"
    ejecutar_escenario(monkeypatch, comprobar)


def test_desconexion_reconexion_y_borrado_del_cliente(monkeypatch):
    """Los callbacks reales cancelan tareas y reconectar solicita una respuesta nueva."""
    async def comprobar(vista):
        """Ejercita el ciclo de vida sin simular que constituye una interrupción de red real."""
        vista.expresion.set_value("x")
        panel = vista.vista_previa
        await panel.tarea
        respuesta = panel.respuesta
        vista._desconectar()
        assert panel.tarea is None and panel.respuesta is None
        await panel.actualizar()
        assert panel.respuesta is None
        vista._reconectar()
        await panel.tarea
        assert panel.respuesta is not respuesta and panel.respuesta["estado"] == "EXITO"
        panel.programar()
        tarea = panel.tarea
        for manejador in panel.minimo.client.delete_handlers:
            manejador()
        await asyncio.gather(tarea, return_exceptions=True)
        assert tarea.cancelled() and panel.tarea is None and panel.respuesta is None
    ejecutar_escenario(monkeypatch, comprobar)
