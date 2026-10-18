"""Panel de Glosa con presentación lateral y modal clásica."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from nicegui import app, ui

from src.ai.contexto import CapturaPaso, ReferenciaPaso, serializar_contexto
from src.ai.cliente_openrouter import ClienteOpenRouter
from src.ai.historial import limpiar_historial_almacenado
from src.frontend import banderas
from src.frontend.componentes.panel_ia_clasico import (
    actualizar_visibilidad_clasico,
    construir_panel_clasico,
    renderizar_chat_clasico,
    renderizar_mensaje_clasico,
)
from src.frontend.componentes.glosa_panel_lateral import PanelLateralGlosaMixin
from src.frontend.constantes import ANTIRREBOTE_IA_SEGUNDOS, MAXIMO_HISTORIAL

registro = logging.getLogger(__name__)


def _inicializar_almacen_historial(almacen: Any) -> None:
    """Inicializa las claves requeridas en el almacen de sesion y poda historial."""
    historial = limpiar_historial_almacenado(almacen.get("ia_historial_chat", []), MAXIMO_HISTORIAL)
    if historial and historial[0].get("texto", "").startswith("¡Hola! Estoy aquí"):
        historial = historial[1:]
    almacen["ia_historial_chat"] = historial
    almacen.setdefault("ia_panel_abierto", False)
    almacen.setdefault("ia_contexto_habilitado", True)


def _recopilar_contexto_didactico(interfaz_activa: Any, foco_explicacion: dict[str, Any] | None) -> str:
    """Serializa el contexto didactico del ejercicio actual agregando el foco activo."""
    if not hasattr(interfaz_activa, "obtener_contexto_ia"):
        return ""
    try:
        contexto = interfaz_activa.obtener_contexto_ia()
        if contexto is None or getattr(contexto, "vacio", False):
            return ""

        if foco_explicacion:
            columnas_foco = tuple(foco_explicacion["columnas"]) if foco_explicacion.get("columnas") else None
            contexto.foco = ReferenciaPaso(
                indice=foco_explicacion["indice"],
                total=foco_explicacion["total"],
                tipo=foco_explicacion["tipo"],
                operacion=foco_explicacion["operacion"],
                captura=CapturaPaso(
                    filas_antes=foco_explicacion.get("filas_antes", {}),
                    filas_despues=foco_explicacion.get("filas_despues", {}),
                    columnas=columnas_foco, detalle=foco_explicacion.get("detalle"),
                ),
            )
        return serializar_contexto(contexto)
    except Exception:
        registro.exception("Error al recopilar el contexto para la IA")
        ui.notify("No pudimos leer tu ejercicio; enviamos solo tu pregunta.", type="warning")
        return ""


class PanelIA(PanelLateralGlosaMixin):
    """Coordina la interfaz de Glosa en modalidades lateral y flotante."""

    @property
    def _almacen(self) -> Any:
        try:
            app.storage.user.get("__test_storage__")
            return app.storage.user
        except Exception as error:
            if not hasattr(self, "_aviso_almacen"):
                registro.warning("Almacen de usuario no disponible: %s. Usando cliente.", error)
                self._aviso_almacen = True
            return app.storage.client

    @property
    def esta_abierto(self) -> bool:
        """Indica si el panel clásico está abierto; el estado lateral se consulta en HTML."""
        return self._almacen.get("ia_panel_abierto", False)

    @esta_abierto.setter
    def esta_abierto(self, valor: bool) -> None:
        """Indica si el panel de Glosa está abierto en la sesión."""
        self._almacen["ia_panel_abierto"] = valor

    @property
    def historial_chat(self) -> list[dict[str, Any]]:
        """Accede al historial de conversación de la sesión."""
        if "ia_historial_chat" not in self._almacen:
            self._almacen["ia_historial_chat"] = []
        return self._almacen["ia_historial_chat"]

    @historial_chat.setter
    def historial_chat(self, valor: list[dict[str, Any]]) -> None:
        """Accede al historial de conversación de la sesión."""
        self._almacen["ia_historial_chat"] = valor

    def __init__(self, interfaz_activa: Any):
        try:
            self._cliente = ui.context.client
        except Exception:
            self._cliente = None

        self.interfaz_activa = interfaz_activa
        self.motor_ia = ClienteOpenRouter()
        self.contenedor_panel = None
        self.superposicion = None
        self.area_chat = None
        self.campo_entrada = None
        self.capsula_contexto = None
        self.contexto_adjuntado = ""
        _inicializar_almacen_historial(self._almacen)
        self._ultimo_envio = 0.0
        self._version_contexto = 0

    def alternar(self) -> None:
        """Abre o cierra el asistente Glosa segun la modalidad activa."""
        if banderas.panel_lateral_habilitado():
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.alternar();")
            return
        self.esta_abierto = not self.esta_abierto
        actualizar_visibilidad_clasico(self)

    def abrir(self) -> None:
        """Abre explicitamente el asistente si se encuentra cerrado."""
        if banderas.panel_lateral_habilitado():
            ui.run_javascript("if(window.scalaris && window.scalaris.glosa) window.scalaris.glosa.abrir();")
            return
        if not self.esta_abierto:
            self.alternar()

    def programar_actualizacion_contexto(self) -> None:
        """Programa el refresco de la píldora de contexto con antirrebote tras cada cambio."""
        if not banderas.panel_lateral_habilitado():
            return

        tarea = getattr(self, "_tarea_actualizacion", None)
        if tarea and not tarea.done():
            tarea.cancel()

        async def _actualizar_con_espera():
            try:
                await asyncio.sleep(ANTIRREBOTE_IA_SEGUNDOS)
                self.notificar_cambio_contexto()
            except asyncio.CancelledError:
                pass
            except Exception as error:
                registro.warning("No se pudo actualizar el contexto de Glosa: %s", type(error).__name__)

        corrutina = _actualizar_con_espera()
        try:
            self._tarea_actualizacion = self._lanzar_tarea(corrutina)
        except RuntimeError:
            corrutina.close()

    def _recopilar_contexto(self) -> str:
        """Serializa el contexto didactico del ejercicio actual agregando el foco activo."""
        if not self._almacen.get("ia_contexto_habilitado", True):
            return ""
        return _recopilar_contexto_didactico(self.interfaz_activa, getattr(self, "foco_explicacion", None))

    def adjuntar_contexto(self) -> None:
        """Adjunta manualmente el contexto textual en la ruta clasico."""
        texto_contexto = self._recopilar_contexto()
        if texto_contexto:
            self.contexto_adjuntado = texto_contexto
            if self.capsula_contexto:
                self.capsula_contexto.set_visibility(True)
            ui.notify("Contexto adjuntado", type="positive")
        else:
            ui.notify("No hay datos validos para adjuntar en la vista actual.", type="warning")

    def limpiar_contexto(self) -> None:
        """Desvincula el contexto manual en la ruta clasico."""
        self.contexto_adjuntado = ""
        if self.capsula_contexto:
            self.capsula_contexto.set_visibility(False)

    def limpiar_chat(self) -> None:
        """Vacia el historial de mensajes retenido."""
        self.historial_chat = []
        if banderas.panel_lateral_habilitado():
            self.renderizar_chat_lateral()
        else:
            self.renderizar_chat()

    def renderizar_chat(self) -> None:
        """Renderiza la bitacora segun la modalidad activa."""
        if banderas.panel_lateral_habilitado():
            self.renderizar_chat_lateral()
        else:
            renderizar_chat_clasico(self)

    def _renderizar_mensaje(self, mensaje: dict[str, Any], indice: int | None = None) -> None:
        """Delega el renderizado individual de mensaje al submodulo clasico."""
        renderizar_mensaje_clasico(mensaje, indice=indice)

    def renderizar_sugerencias_en_linea(self, limite: int = 2) -> None:
        """Renderiza sugerencias incrustadas en el flujo principal de la pagina."""
        from src.frontend.sugerencias import sugerencias_activas, sugerir
        if not sugerencias_activas() or not hasattr(self.interfaz_activa, "obtener_senales_ia"):
            return

        senales = self._obtener_senales_interfaz()
        if not senales:
            return

        habilitado = self._almacen.get("ia_contexto_habilitado", True)
        sugerencias = sugerir(senales, limite=limite, incluir_especificas=habilitado)
        if not sugerencias:
            return

        from src.frontend.componentes.glosa_sugerencias import renderizar_fila_sugerencias
        enviando = getattr(self, "_esta_enviando", False)
        renderizar_fila_sugerencias(sugerencias, self.preguntar_sugerencia, variante="en_linea", deshabilitado=enviando)

    def construir(self) -> None:
        """Construye la presentación lateral o el modal clásico de Glosa según la configuración."""
        if self._cliente is None:
            try:
                self._cliente = ui.context.client
            except Exception:
                pass

        if banderas.panel_lateral_habilitado():
            self.construir_panel_lateral()
        else:
            construir_panel_clasico(self)
