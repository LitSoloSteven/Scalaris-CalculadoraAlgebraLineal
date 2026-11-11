"""Identidad de publicación común a la exploración y al lote de regla falsa."""
import asyncio
from dataclasses import dataclass

from nicegui import ui

from src.ai.huellas import calcular_huella


@dataclass(frozen=True)
class SolicitudPanel:
    """Identifica el trabajo por tarea, revisión, destino y captura al iniciarlo."""

    tarea: asyncio.Task | None
    revision: int
    destino: ui.column
    captura: dict
    huella: str

    def corresponde(self, panel) -> bool:
        """Indica si la solicitud todavía corresponde al destino y captura del panel."""
        return (not panel._cerrado and self.tarea is panel.tarea and self.revision == panel._revision
                and self.destino is panel.contenedor_resultados and not self.destino.is_deleted
                and self.huella == calcular_huella(panel.capturar()))


def iniciar_solicitud(panel) -> SolicitudPanel:
    """Identifica la espera actual y activa su estado de carga."""
    captura = panel.capturar()
    panel.tarea = asyncio.current_task()
    panel._mostrar_carga(True)
    return SolicitudPanel(panel.tarea, panel._revision, panel.contenedor_resultados, captura, calcular_huella(captura))


def revocar_solicitud(panel) -> None:
    """Invalida publicación y espera sin cancelar el trabajador real del coordinador."""
    panel._revision += 1
    panel.coordinador.invalidar()
    if panel.tarea is not None:
        panel.tarea.cancel()
        panel.tarea = None
