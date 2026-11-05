"""Vigencia de la consulta de continuidad en la captura real."""
import asyncio

from nicegui import run

from src.frontend.controladores.biseccion.continuidad_intervalo import consultar_continuidad
from tests.comun_biseccion_criterios import captura_criterio, ejecutar_escenario


def test_continuidad_previa_descarta_respuesta_fuera_de_orden(monkeypatch):
    """Una respuesta retenida no reaparece al editar y restaurar una captura."""
    async def comprobar(vista):
        """Retiene la consulta anterior mientras se completa la nueva."""
        inicio, liberar = asyncio.Event(), asyncio.Event()
        contador = 0

        async def trabajar(calcular, captura):
            """Devuelve una marca distinguible solo para la consulta antigua."""
            nonlocal contador
            if calcular is consultar_continuidad:
                contador += 1
                if contador == 1:
                    inicio.set()
                    try:
                        await liberar.wait()
                    except asyncio.CancelledError:
                        await liberar.wait()
                    return {"informe": {**calcular(captura)["informe"], "mensaje": "Informe antiguo"}}
            return calcular(captura)

        monkeypatch.setattr(run, "io_bound", trabajar)
        vista.cargar_captura(captura_criterio())
        panel = vista.continuidad
        anterior = panel.tarea
        await inicio.wait()
        vista.superior.set_value("3")
        vista.superior.set_value("2")
        await panel.tarea
        liberar.set()
        await anterior
        informe = panel.respuesta["informe"]
        assert informe["estado"] == "CONFIRMADA"
        assert informe["intervalo"] == (1, 2) and informe["mensaje"] != "Informe antiguo"

    ejecutar_escenario(monkeypatch, comprobar)
