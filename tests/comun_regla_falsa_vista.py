"""Escenarios con controles NiceGUI reales y transporte de navegador aislado."""
import asyncio

from nicegui import Client, core, ui

from src.frontend.vistas.regla_falsa.vista_regla_falsa import VistaReglaFalsa
from tests.comun_construccion_vistas import cerrar_cliente, preparar_transporte


def captura_regla_falsa(**cambios):
    """Devuelve un ejercicio del motor real con preferencias reproducibles."""
    return {"expresion": "x^2-2", "extremo_izquierdo": "1", "extremo_derecho": "2",
            "tolerancia": "1e-6", "limite_iteraciones": "100", "unidad_angular": "radianes", **cambios}


def ejecutar_escenario(monkeypatch, comprobar):
    """Monta y destruye la vista sin registrar una ruta del producto ni sustituir su motor."""
    async def ejecutar():
        """Mantiene los controles y la comprobación dentro de su cliente NiceGUI."""
        monkeypatch.setattr(core, "script_mode", False)
        cliente = Client(ui.page("/prueba_regla_falsa"))
        preparar_transporte(monkeypatch, cliente)
        vista = VistaReglaFalsa()
        try:
            with cliente:
                vista.construir()
                await comprobar(vista)
        finally:
            await cerrar_cliente(cliente, [vista])
    asyncio.run(ejecutar())


def textos_resultado(vista) -> list[str]:
    """Devuelve textos de los elementos vigentes del resultado sin interpretar HTML."""
    return [str(elemento.text) for elemento in vista.contenedor_resultados.descendants()
            if hasattr(elemento, "text")]
