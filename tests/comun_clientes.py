"""Clientes y paneles simulados compartidos por las pruebas de interfaz."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.frontend.componentes.panel_ia import PanelIA
from src.frontend.rutas import registrar_redirecciones_heredadas


class ClienteSimulado:
    """Registra entradas de contexto y JavaScript de la API NiceGUI."""

    def __init__(self):
        self.entradas = 0
        self.salidas = 0
        self.llamadas_js = []
        self.is_deleted = False

    def __enter__(self):
        self.entradas += 1
        return self

    def __exit__(self, *argumentos):
        self.salidas += 1

    def run_javascript(self, codigo: str, *, timeout: float = 1.0):
        """Registra el código recibido por la API de cliente de NiceGUI."""
        self.llamadas_js.append(codigo)


class PanelIASimulado(PanelIA):
    """Panel de IA cuyo almacenamiento se inyecta sin una sesión real."""

    def __init__(self, interfaz=None, almacen=None):
        self._almacen_simulado = almacen if almacen is not None else {"ia_contexto_habilitado": True}
        super().__init__(interfaz)

    @property
    def _almacen(self):
        return self._almacen_simulado


def crear_cliente_redirecciones():
    """Crea una aplicación mínima que expone las redirecciones registradas."""
    aplicacion = FastAPI()
    registrar_redirecciones_heredadas(aplicacion)
    return TestClient(aplicacion, follow_redirects=False)
