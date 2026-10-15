"""Selector de método y banner de recomendación para la vista de Determinantes."""
from __future__ import annotations

from typing import Any

from nicegui import ui

from src.frontend.controllers.determinant_ops import DeterminantOpsController
from src.frontend.controllers.determinant_ops._config import COFACTORES_MAX_N, METODOS

METODO_COFACTORES, METODO_LU = METODOS
NOMBRES_METODO = {METODO_COFACTORES: "Cofactores", METODO_LU: "Eliminación"}
MENSAJE_LIMITE_COFACTORES = f"Cofactores admite hasta {COFACTORES_MAX_N}×{COFACTORES_MAX_N}"
MENSAJE_CAMBIO_A_ELIMINACION = (
    f"Pasamos a eliminación: cofactores admite hasta {COFACTORES_MAX_N}×{COFACTORES_MAX_N}."
)


class DeterminantOpsMetodoMixin:
    """Gestiona la elección de método y la recomendación según la dimensión.

    Requiere en la vista: square_panel, method_tabs, tab_cofactores, reco_container,
    _clave_recomendacion y _tooltip_cofactores, además de _atenuar_resultado y
    _refrescar_glosa, definidos en los mixins de resultado y de Glosa.
    """

    def _construir_selector_metodo(self) -> None:
        """Crea las pestañas de método y el contenedor del banner de recomendación."""
        with ui.tabs().classes("neo-tabs method-tabs").props("dense no-caps") as self.method_tabs:
            self.tab_cofactores = ui.tab(
                METODO_COFACTORES, label=NOMBRES_METODO[METODO_COFACTORES]
            )
            ui.tab(METODO_LU, label=NOMBRES_METODO[METODO_LU])
        self.method_tabs.value = METODO_COFACTORES
        self.method_tabs.on_value_change(self._on_metodo_change)
        self.reco_container = (
            ui.element("div")
            .classes("det-reco w-full")
            .props('role="status" aria-live="polite"')
        )

    def _actualizar_recomendacion(self) -> None:
        """Repinta el banner solo cuando cambia la dimensión o el método elegido."""
        if self.reco_container is None:
            return
        n = self.square_panel.n
        metodo = self.method_tabs.value
        clave = (n, metodo)
        if clave == self._clave_recomendacion:
            return
        self._clave_recomendacion = clave
        recomendacion = DeterminantOpsController.recomendar(n)
        self.reco_container.clear()
        with self.reco_container:
            self._pintar_recomendacion(n, metodo, recomendacion)

    def _pintar_recomendacion(self, n: int, metodo: str, recomendacion: dict[str, Any]) -> None:
        """Dibuja el texto de la recomendación y, si aplica, el botón para adoptarla."""
        recomendado = recomendacion.get("recommended", METODO_LU)
        with ui.column().classes("det-reco-texto gap-1"):
            ui.label(
                f"Para n = {n} recomendamos {NOMBRES_METODO.get(recomendado, recomendado)}."
            ).classes("font-semibold text-main")
            ui.label(str(recomendacion.get("reason", ""))).classes("text-sec fs-small")
        disponible = recomendado != METODO_COFACTORES or recomendacion.get(
            "cofactor_available", False
        )
        if metodo != recomendado and disponible:
            ui.button(
                "Usar el recomendado",
                on_click=lambda: self._seleccionar_metodo(recomendado),
                color=None,
            ).classes("btn-ghost det-reco-accion").props("ripple=false")

    def _seleccionar_metodo(self, metodo: str) -> None:
        """Cambia la pestaña activa al método indicado."""
        self.method_tabs.value = metodo

    def _aplicar_disponibilidad_metodo(self) -> None:
        """Habilita o deshabilita cofactores según la dimensión actual."""
        if self.square_panel.n > COFACTORES_MAX_N:
            self._deshabilitar_cofactores()
        else:
            self._habilitar_cofactores()

    def _deshabilitar_cofactores(self) -> None:
        """Bloquea la pestaña de cofactores y pasa a eliminación si estaba activa."""
        self.tab_cofactores.props("disable")
        if self._tooltip_cofactores is None:
            with self.tab_cofactores:
                self._tooltip_cofactores = ui.tooltip(MENSAJE_LIMITE_COFACTORES)
        if self.method_tabs.value == METODO_COFACTORES:
            ui.notify(MENSAJE_CAMBIO_A_ELIMINACION, type="info")
            self.method_tabs.value = METODO_LU

    def _habilitar_cofactores(self) -> None:
        """Rehabilita la pestaña de cofactores sin tocar la selección actual."""
        self.tab_cofactores.props(remove="disable")
        if self._tooltip_cofactores is not None:
            self._tooltip_cofactores.delete()
            self._tooltip_cofactores = None

    def _on_metodo_change(self, e: Any) -> None:
        """Reacciona al cambio de método: atenúa el resultado y actualiza banner y Glosa."""
        if not e.value:
            return
        self._atenuar_resultado()
        self._actualizar_recomendacion()
        self._refrescar_glosa()
