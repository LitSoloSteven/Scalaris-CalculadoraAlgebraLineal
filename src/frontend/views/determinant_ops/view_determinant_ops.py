"""Vista principal del módulo de Determinantes de Scalaris."""
from __future__ import annotations

import itertools
import logging
from typing import Any

from nicegui import ui

from src.frontend.components.ai_panel import AIPanel
from src.frontend.components.app_shell import create_app_shell
from src.frontend.components.calculator import CalculatorPanel
from src.frontend.components.handoff import (
    clean_handoff_url,
    consume_matrix,
    render_handoff_notice,
)
from src.frontend.components.historial_calculos import HistorialCalculos
from src.frontend.components.square_matrix_panel import SquareMatrixPanel
from src.frontend.controllers.determinant_ops._config import COFACTORES_MAX_N, LU_MAX_N
from src.frontend.navigation import route_of
from src.frontend.views.determinant_ops._config import (
    HISTORIAL_MAX,
    ID_BOTON_LIMPIAR,
    ID_RESULTADOS,
)
from src.frontend.views.determinant_ops.ai_mixin import DeterminantOpsAiMixin
from src.frontend.views.determinant_ops.calculo_mixin import DeterminantOpsCalculoMixin
from src.frontend.views.determinant_ops.metodo_mixin import (
    METODO_COFACTORES,
    DeterminantOpsMetodoMixin,
)
from src.frontend.views.determinant_ops.preview_mixin import DeterminantOpsPreviewMixin
from src.frontend.views.determinant_ops.render_mixin import DeterminantOpsRenderMixin
from src.frontend.views.determinant_ops.steps_mixin import DeterminantOpsStepsMixin

logger = logging.getLogger(__name__)

HOJA_ESTILOS = "/assets/css/determinantes.css"
MENSAJE_HISTORIAL_VACIO = "No hay determinantes calculados en esta sesión."
MENSAJE_RESTAURAR_FALLIDO = "No se pudo restaurar la matriz. Inténtalo de nuevo."


class DeterminantOpsUI(
    DeterminantOpsCalculoMixin,
    DeterminantOpsRenderMixin,
    DeterminantOpsStepsMixin,
    DeterminantOpsPreviewMixin,
    DeterminantOpsMetodoMixin,
    DeterminantOpsAiMixin,
):
    """Compone la vista de Determinantes a partir de sus mixins de responsabilidad única."""

    def __init__(self) -> None:
        """Crea los componentes compartidos y deja en None los elementos de interfaz."""
        self.square_panel = SquareMatrixPanel()
        self.calculator = CalculatorPanel()
        self.historial = HistorialCalculos(
            al_restaurar=self._restaurar_historial,
            vacio=MENSAJE_HISTORIAL_VACIO,
            maximo=HISTORIAL_MAX,
        )
        self.ai_panel: AIPanel | None = None
        self.reproductor_pasos = None
        self.last_result: dict[str, Any] | None = None
        self._result_fp: str | None = None
        self.preview_task = None
        self.contenedor_resultados: ui.column | None = None
        self.preview_container: ui.column | None = None
        self.tools_tabs: ui.tabs | None = None
        self.method_tabs: ui.tabs | None = None
        self.tab_cofactores: ui.tab | None = None
        self.reco_container: ui.element | None = None
        self.handoff_slot: ui.column | None = None
        self._clave_recomendacion: tuple[int, str] | None = None
        self._tooltip_cofactores: ui.tooltip | None = None
        self._uid_counter = itertools.count()

    def _restaurar_historial(self, datos: dict[str, Any]) -> None:
        """Restaura la matriz y el método guardados en una entrada del historial.

        Args:
            datos: Diccionario con las claves "data" (matriz de textos) y "metodo".
        """
        try:
            matriz = datos["data"]
            self.square_panel.set_data(matriz)
            if len(matriz) <= COFACTORES_MAX_N or datos["metodo"] != METODO_COFACTORES:
                self.method_tabs.value = datos["metodo"]
        except (KeyError, TypeError, ValueError):
            logger.error("No se pudo restaurar el historial de determinantes", exc_info=True)
            ui.notify(MENSAJE_RESTAURAR_FALLIDO, type="negative", position="top")

    def build(self, handoff_token: str = "") -> None:
        """Construye la página completa de Determinantes.

        Args:
            handoff_token: Token opcional para cargar una matriz enviada desde otra herramienta.
        """
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of("determinantes"))
        self.square_panel.inject_scripts()
        self.square_panel.on_data_change = self._on_matrix_change
        self.calculator.inject_scripts()
        ui.add_head_html(f'<link rel="stylesheet" href="{HOJA_ESTILOS}">')

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            self.handoff_slot = ui.column().classes("w-full")
            self._construir_encabezado()
            with ui.element("div").classes("layout-split mb-8"):
                self._construir_panel_captura()
                self._construir_panel_herramientas()
            self._construir_contenedor_resultados()

        self.ai_panel.build()
        self._aplicar_disponibilidad_metodo()
        self._actualizar_recomendacion()
        self._consumir_handoff(handoff_token)

    def _construir_encabezado(self) -> None:
        """Dibuja el título y el subtítulo de la vista."""
        with ui.column().classes("mb-8"):
            ui.label("Determinantes").classes("text-2xl font-bold text-main")
            ui.label("Cofactores o eliminación con pivoteo").classes(
                "fs-small text-sec uppercase"
            ).style("letter-spacing: 0.08em;")

    def _construir_panel_captura(self) -> None:
        """Dibuja el selector de método, la matriz y los botones de acción."""
        with ui.column().classes("layout-pane"):
            with ui.column().classes("w-full gap-3 mb-4"):
                self._construir_selector_metodo()
            self.square_panel.build_container()
            with ui.row().classes("w-full mt-6 gap-4"):
                ui.button(
                    icon="delete", on_click=self.confirmar_limpieza, color=None
                ).classes("btn-ghost flex-1 py-3").props(
                    f'ripple=false id="{ID_BOTON_LIMPIAR}" aria-label="Limpiar"'
                ).tooltip("Limpiar")
                ui.button(
                    "Calcular determinante",
                    on_click=lambda e: self.calcular(e.sender),
                    color=None,
                ).classes("btn-primary flex-[2] py-3").props("ripple=false")

    def _construir_panel_herramientas(self) -> None:
        """Dibuja las pestañas de teclado, vista previa e historial."""
        with ui.column().classes("layout-pane tools-panel"):
            with ui.tabs().classes("neo-tabs w-full").props("dense no-caps") as self.tools_tabs:
                ui.tab("teclado", label="Teclado")
                ui.tab("preview", label="Vista previa")
                ui.tab("history", label="Historial")
            self.tools_tabs.on_value_change(
                lambda e: self._trigger_live_preview() if e.value == "preview" else None
            )
            with ui.tab_panels(self.tools_tabs, value="teclado").classes(
                "w-full p-0 bg-transparent"
            ).props("animated"):
                with ui.tab_panel("teclado").classes("p-0 mt-4"):
                    self.calculator.build(None)
                with ui.tab_panel("preview").classes(
                    "p-6 panel-card mt-4 min-h-[300px] items-center"
                ):
                    ui.label("Vista previa en vivo").classes("font-bold text-main mb-4")
                    self.preview_container = ui.column().classes(
                        "w-full items-center justify-center"
                    )
                    self._trigger_live_preview()
                with ui.tab_panel("history").classes("p-6 panel-card mt-4 min-h-[300px]"):
                    ui.label("Últimos determinantes calculados").classes(
                        "font-bold text-main mb-4"
                    )
                    self.historial.construir()

    def _construir_contenedor_resultados(self) -> None:
        """Crea la tarjeta de resultados y la deja en su estado inicial."""
        self.contenedor_resultados = ui.column().classes(
            "w-full panel-card p-6 items-center justify-center min-h-[400px]"
        ).props(f'id="{ID_RESULTADOS}"')
        self.reset_resultados()

    def _consumir_handoff(self, token: str) -> None:
        """Carga la matriz enviada desde otra herramienta y avisa del resultado."""
        traspaso = consume_matrix(token, max_n=LU_MAX_N)
        if traspaso is None:
            return
        with self.handoff_slot:
            n = len(traspaso.data) if traspaso.data else 0
            render_handoff_notice(
                traspaso,
                f"Cargamos A ({n}×{n}) desde {traspaso.source_name}. "
                "Presiona Calcular determinante para continuar.",
            )
        if traspaso.status == "ok":
            self.square_panel.set_data(traspaso.data)
        clean_handoff_url()
