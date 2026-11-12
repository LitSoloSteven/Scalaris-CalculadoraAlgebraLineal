"""Región de continuidad del intervalo activo y presentación de su evidencia."""
import asyncio

from nicegui import ui
from src.frontend.componentes.informe_continuidad_raices import mostrar_informe_continuidad

from src.frontend.constantes import ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS
from src.frontend.controladores.actualizacion_cancelable import programar_actualizacion
from src.frontend.controladores.biseccion.continuidad_intervalo import consultar_continuidad
from src.frontend.controladores.biseccion.vigencia_panel import invalidar_panel
from src.frontend.controladores.calculo_vigente import ejecutar_calculo_vigente

_CLAVES = ("expresion", "extremo_izquierdo", "extremo_derecho", "unidad_angular", "cero_preferido")


def mostrar_informe(informe: dict) -> None:
    """Presenta el estado y la evidencia que el dominio asoció al intervalo."""
    mostrar_informe_continuidad(informe, "biseccion-numero texto-principal")


class PanelContinuidad:
    """Consulta solo cuando cambia la función, la unidad o el intervalo."""

    def __init__(self, vista):
        self.vista = vista
        self.tarea = self.respuesta = None
        self._revision_captura = self._identificador_calculo = 0
        self._cerrado = False
        self._clave = None

    def construir(self) -> None:
        """Monta una región viva que permanece estable durante las consultas."""
        self.contenedor_resultados = ui.column().classes("w-full gap-1").props("role=status aria-live=polite")
        ui.context.client.on_delete(self.cerrar)
        self.programar()

    def capturar(self) -> dict:
        """Extrae los campos que determinan el diagnóstico."""
        captura = self.vista.capturar()
        return {clave: captura.get(clave) for clave in _CLAVES}

    def programar(self) -> None:
        """Sustituye un diagnóstico obsoleto y espera a que termine la edición."""
        captura = self.capturar()
        if self._cerrado or self.contenedor_resultados.is_deleted or captura == self._clave:
            return
        self._clave = captura
        invalidar_panel(self)
        campos = tuple(str(captura[clave]).strip() if captura[clave] is not None else "" for clave in _CLAVES[:3])
        if not any(campos):
            self._mostrar()
        elif not all(campos):
            self._mostrar("Completa la función y los extremos para consultar la continuidad.")
        else:
            self._mostrar("Consultando la continuidad del intervalo…")
            self.tarea = programar_actualizacion(None, self._consultar, lambda: not self._cerrado,
                                                  ANTIRREBOTE_VISTA_PREVIA_SEGUNDOS)

    async def _consultar(self) -> None:
        tarea = asyncio.current_task()
        try:
            vigente = await ejecutar_calculo_vigente(self, self.capturar, consultar_continuidad)
            if vigente and self.tarea is tarea:
                self.respuesta = vigente[0]
                self._mostrar(self.respuesta.get("mensaje"), self.respuesta.get("informe"))
        except Exception:
            if self.tarea is tarea:
                self._mostrar("No se pudo consultar la continuidad. Revisa la función y los extremos.")
        finally:
            if self.tarea is tarea:
                self.tarea = None

    def _mostrar(self, mensaje: str | None = None, informe: dict | None = None) -> None:
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            if informe is not None:
                mostrar_informe(informe)
            elif mensaje:
                ui.label(mensaje).classes("text-sm texto-secundario")

    def cerrar(self) -> None:
        """Revoca la espera y descarta la huella al desconectar."""
        self._cerrado = True
        self._clave = None
        invalidar_panel(self)

    def reabrir(self) -> None:
        """Vuelve a consultar la captura al reconectar."""
        self._cerrado = False
        self.programar()
