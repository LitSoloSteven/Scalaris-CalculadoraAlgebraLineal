"""Escenarios aislados del formulario real de bisección con transporte simulado."""
import asyncio

from nicegui import Client, core, ui

from src.frontend.vistas.biseccion.vista_biseccion import VistaBiseccion
from tests.comun_construccion_vistas import preparar_transporte, cerrar_cliente


def captura_criterio(tipo="decimales", parametro=4):
    """Devuelve un ejercicio reproducible con un criterio explícito y preferencias heredadas."""
    return {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2",
            "decimales": 4, "limite_iteraciones": 100, "criterio": {"tipo": tipo, "parametro": parametro}}


def ejecutar_escenario(monkeypatch, comprobar):
    """Construye y destruye una vista real para ejecutar una comprobación asíncrona sin red."""
    async def ejecutar():
        """Conserva el ciclo de vida de NiceGUI con trabajadores y transporte aislados."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/prueba_selector_biseccion"))
        preparar_transporte(monkeypatch, cliente)
        vista = VistaBiseccion()
        try:
            with cliente:
                vista.construir()
                await comprobar(vista)
        finally:
            await cerrar_cliente(cliente, [vista])
    asyncio.run(ejecutar())
