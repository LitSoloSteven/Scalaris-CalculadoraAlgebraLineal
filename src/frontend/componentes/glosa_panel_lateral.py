"""Componente principal PanelLateralGlosaMixin para el asistente flotante y lateral."""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from nicegui import ui

from src.frontend.componentes.glosa_bitacora import (
    construir_bitacora_lateral,
    desplazar_al_final,
    renderizar_bitacora_lateral,
)
from src.frontend.componentes.glosa_cabecera import construir_cabecera_lateral
from src.frontend.componentes.glosa_sugerencias import renderizar_fila_sugerencias
from src.frontend.componentes.glosa_envio import EnvioGlosaMixin
from src.frontend.componentes.glosa_foco import FocoGlosaMixin
from src.frontend.componentes.glosa_pie import (
    construir_boton_y_fondo,
    construir_pie_lateral,
    renderizar_pildora_contexto,
)
from src.frontend.componentes.tareas import lanzar_tarea
from src.frontend.sugerencias import sugerencias_activas, sugerir

registro = logging.getLogger(__name__)


class PanelLateralGlosaMixin(FocoGlosaMixin, EnvioGlosaMixin):
    """Ensambla la cabecera, bitácora y pie del panel lateral de Glosa."""

    def _lanzar_tarea(self, corrutina: Any) -> asyncio.Task:
        """Devuelve una tarea asíncrona asociada al cliente para ejecutar la corrutina recibida."""
        return lanzar_tarea(getattr(self, "_cliente", None), corrutina)

    def _enviar_mensaje_asincrono(self, texto: str) -> asyncio.Task:
        """Devuelve la tarea de consulta iniciada en el contexto de este cliente."""
        return self._lanzar_tarea(self._enviar_consulta(texto))

    def construir_panel_lateral(self) -> None:
        """Construye la estructura del panel lateral accesible."""
        with ui.element("aside").classes("glosa-panel-lateral flex flex-col no-wrap").props(
            'id="glosa-panel-lateral" tabindex="-1" role="complementary" aria-label="Glosa, asistente de álgebra lineal" data-glosa-conservar'
        ):
            construir_cabecera_lateral(self.limpiar_chat)
            self.area_chat = construir_bitacora_lateral()
            self.renderizar_chat_lateral()
            construir_pie_lateral(self)

        construir_boton_y_fondo()

    def _alternar_contexto(self, evento: Any) -> None:
        """Alterna la inclusión automática de contexto algebraico."""
        self._almacen["ia_contexto_habilitado"] = evento.value
        self.renderizar_pildora_contexto.refresh()

    @ui.refreshable
    def renderizar_pildora_contexto(self) -> None:
        """Refresca la píldora de contexto en el pie del panel lateral."""
        renderizar_pildora_contexto(self)

    def notificar_cambio_contexto(self) -> None:
        """Notifica al panel lateral que el contexto del ejercicio cambió."""
        if hasattr(self, "_version_contexto"):
            self._version_contexto += 1
        self.renderizar_pildora_contexto.refresh()
        self._renderizar_sugerencias_laterales()

    def _renderizar_sugerencias_laterales(self) -> None:
        """Actualiza la lista de preguntas sugeridas en base a señales de la interfaz."""
        if not hasattr(self, "contenedor_sugerencias") or not self.contenedor_sugerencias:
            return
        if not sugerencias_activas():
            self.contenedor_sugerencias.clear()
            return

        senales = self._obtener_senales_interfaz()
        habilitado = self._almacen.get("ia_contexto_habilitado", True)
        sugerencias = sugerir(senales, limite=3, incluir_especificas=habilitado)
        identificadores = tuple(sugerencia.identificador for sugerencia in sugerencias)

        if identificadores == getattr(self, "_identificadores_sugerencias", ()) and not getattr(self, "_forzar_sugerencias", False):
            return

        self._identificadores_sugerencias = identificadores
        self._forzar_sugerencias = False
        self.contenedor_sugerencias.clear()
        if not sugerencias:
            return

        with self.contenedor_sugerencias:
            enviando = getattr(self, "_esta_enviando", False)
            renderizar_fila_sugerencias(sugerencias, self.preguntar_sugerencia, variante="panel_lateral", deshabilitado=enviando)

    def _obtener_senales_interfaz(self) -> Any:
        """Recupera con tolerancia a fallos las señales didácticas del ejercicio activo."""
        if hasattr(self.interfaz_activa, "obtener_senales_ia"):
            try:
                return self.interfaz_activa.obtener_senales_ia()
            except Exception as error:
                registro.error("Error en obtener_senales_ia: %s", type(error).__name__)
        return None

    def renderizar_chat_lateral(self) -> None:
        """Invoca el renderizado reactivo del área de bitácora."""
        renderizar_bitacora_lateral(self)

    def _desplazar_al_final(self) -> None:
        """Desplaza el scroll de la bitácora al extremo inferior."""
        desplazar_al_final(self)
