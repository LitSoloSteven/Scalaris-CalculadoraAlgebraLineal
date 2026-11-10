"""Coordinación acotada probada desde la vista real y su ciclo de cliente."""
import asyncio

import pytest
from nicegui import run, ui

from tests.comun_regla_falsa_vista import ejecutar_escenario
from tests.test_regla_falsa_exploracion import preparar_busqueda


def retener_trabajador(monkeypatch):
    """Retiene el primer trabajo con eventos, registra capturas y mide concurrencia real."""
    inicio, liberar = asyncio.Event(), asyncio.Event()
    datos = {"capturas": [], "activos": 0, "maximo": 0}

    async def trabajar(calcular, captura):
        """Conserva la plaza hasta la liberación explícita y usa el controlador real."""
        datos["capturas"].append(captura)
        datos["activos"] += 1
        datos["maximo"] = max(datos["maximo"], datos["activos"])
        try:
            inicio.set()
            await liberar.wait()
            return calcular(captura)
        finally:
            datos["activos"] -= 1
    monkeypatch.setattr(run, "io_bound", trabajar)
    return inicio, liberar, datos


def test_cincuenta_ediciones_no_acumulan_trabajadores_en_la_vista(monkeypatch):
    """El panel conserva un trabajador y el último borrador tras cincuenta solicitudes."""
    async def comprobar(vista):
        """Retiene el primer escaneo mientras reemplaza y revoca capturas posteriores."""
        panel = preparar_busqueda(vista)
        inicio, liberar, datos = retener_trabajador(monkeypatch)
        antigua = asyncio.create_task(panel.enviar_busqueda())
        await inicio.wait()
        for valor in range(1, 51):
            vista.expresion.set_value(f"x-{valor}")
            await antigua
            antigua = asyncio.create_task(panel.enviar_busqueda())
            await asyncio.sleep(0)
            assert panel.coordinador.activos == panel.coordinador.pendientes == 1
            assert panel.respuesta is None
        liberar.set()
        await antigua
        await panel.coordinador.esperar_cierre()
        assert datos["maximo"] == 1
        assert [captura["expresion"] for captura in datos["capturas"]] == ["x^2-2", "x-50"]
        assert panel.respuesta["estado"] == "EXITO" and not panel.respuesta["candidatos"]
        assert panel.boton.enabled and panel.tarea is None
        assert panel.coordinador.activos == panel.coordinador.pendientes == 0
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("reconectar", [False, True])
def test_cierre_descarta_borrador_sin_liberar_trabajo_real(monkeypatch, reconectar):
    """Desconectar borra pendientes y una reconexión nunca publica respuestas anteriores."""
    async def comprobar(vista):
        """Cierra con trabajo real retenido, vuelve a conectar y espera su cierre efectivo."""
        panel = preparar_busqueda(vista)
        inicio, liberar, datos = retener_trabajador(monkeypatch)
        primera = asyncio.create_task(panel.enviar_busqueda())
        await inicio.wait()
        vista.expresion.set_value("x^2-3")
        await primera
        segunda = asyncio.create_task(panel.enviar_busqueda())
        await asyncio.sleep(0)
        vista.cerrar()
        await segunda
        assert panel.coordinador.activos == 1 and panel.coordinador.pendientes == 0
        if reconectar:
            vista.reabrir()
        liberar.set()
        await panel.coordinador.esperar_cierre()
        assert len(datos["capturas"]) == 1 and panel.respuesta is None
        assert not list(panel.contenedor_resultados.descendants())
        if reconectar:
            await panel.enviar_busqueda()
            assert len(datos["capturas"]) == 2 and panel.respuesta["estado"] == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("cambio", ["funcion", "destino", "eliminar", "unidad", "rango", "paso", "limpiar"])
def test_respuesta_retenida_no_publica_tras_cambiar_contexto(monkeypatch, cambio):
    """La respuesta antigua no entrega candidatos a una captura o destino diferentes."""
    async def comprobar(vista):
        """Retiene el servicio y modifica el contexto antes de liberar la respuesta."""
        panel = preparar_busqueda(vista)
        inicio, liberar, datos = retener_trabajador(monkeypatch)
        tarea = asyncio.create_task(panel.enviar_busqueda())
        await inicio.wait()
        if cambio == "funcion":
            vista.expresion.set_value("x^2-3")
        elif cambio == "destino":
            panel.contenedor_resultados = ui.column()
        elif cambio == "eliminar":
            panel.contenedor_resultados.delete()
        elif cambio == "unidad":
            vista.unidad_angular.set_value("grados")
        elif cambio == "rango":
            panel.minimo.set_value("-3")
        elif cambio == "paso":
            panel.paso.set_value(".5")
        else:
            vista.limpiar_todo()
        liberar.set()
        await tarea
        await panel.coordinador.esperar_cierre()
        assert datos["maximo"] == 1 and panel.respuesta is None
        assert panel.tarea is None and panel.boton.enabled
    ejecutar_escenario(monkeypatch, comprobar)


def test_error_inesperado_se_recupera_sin_filtrar_detalles(monkeypatch):
    """La plaza vuelve a aceptar solicitudes después de un fallo de transporte."""
    async def comprobar(vista):
        """Provoca un error privado y ejecuta después una búsqueda válida."""
        panel = preparar_busqueda(vista)

        async def fallar(calcular, captura):
            """Simula una excepción interna antes de recibir la respuesta del controlador."""
            raise RuntimeError("detalle privado")

        with monkeypatch.context() as contexto:
            contexto.setattr(run, "io_bound", fallar)
            await panel.enviar_busqueda()
        assert "No se pudo completar" in panel.estado.text and "privado" not in panel.estado.text
        assert panel.boton.enabled and panel.coordinador.activos == 0
        await panel.enviar_busqueda()
        assert panel.respuesta["estado"] == "EXITO"
    ejecutar_escenario(monkeypatch, comprobar)


@pytest.mark.parametrize("eliminar", [False, True])
def test_error_tardio_no_publica_en_un_destino_distinto(monkeypatch, eliminar):
    """Sustituir o eliminar el destino también revoca los errores del trabajador anterior."""
    async def comprobar(vista):
        """Cambia el contenedor desde el trabajador y provoca después el fallo privado."""
        panel = preparar_busqueda(vista)

        async def fallar(calcular, captura):
            """Deja obsoleto el destino antes de devolver un error inesperado."""
            if eliminar:
                panel.contenedor_resultados.delete()
            else:
                with vista.contenedor_resultados:
                    panel.contenedor_resultados = ui.column()
            raise RuntimeError("detalle privado")

        monkeypatch.setattr(run, "io_bound", fallar)
        await panel.enviar_busqueda()
        assert "No se pudo completar" not in panel.estado.text
        assert panel.respuesta is None and panel.boton.enabled
        assert panel.coordinador.activos == 0
    ejecutar_escenario(monkeypatch, comprobar)
