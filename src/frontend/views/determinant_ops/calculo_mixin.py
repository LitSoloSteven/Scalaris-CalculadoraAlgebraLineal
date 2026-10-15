"""Cálculo, limpieza y reacción a cambios de la vista de Determinantes."""
from __future__ import annotations

import json
import logging
from typing import Any

from nicegui import run, ui

from src.ai.context import fingerprint
from src.frontend.controllers.determinant_ops import DeterminantOpsController
from src.frontend.controllers.determinant_ops._config import ETIQUETAS_METODO
from src.frontend.views.determinant_ops._config import CONFIRMAR_N_GRANDE, ID_RESULTADOS

logger = logging.getLogger(__name__)

ESTADOS_HISTORIAL: dict[str, tuple[str, str]] = {
    "SUCCESS": ("Invertible", "exito"),
    "SINGULAR": ("Singular", "alerta"),
}
MENSAJE_VACIO = "Escribe al menos un valor antes de calcular."
MENSAJE_ERROR_INESPERADO = (
    "Ocurrió un error inesperado al calcular el determinante. "
    "Revisa los datos e inténtalo de nuevo."
)
TIMEOUT_ANIMACION_LIMPIEZA_S = 2.0


class DeterminantOpsCalculoMixin:
    """Coordina el cálculo, la limpieza y la reacción a cambios de la matriz.

    Requiere en la vista: square_panel, method_tabs, contenedor_resultados, historial,
    reproductor_pasos, last_result y _result_fp, además de _render_resultado,
    _atenuar_resultado, _actualizar_recomendacion, _aplicar_disponibilidad_metodo,
    _trigger_live_preview y _refrescar_glosa de los demás mixins.
    """

    def _on_matrix_change(self) -> None:
        """Reacciona a cambios de la matriz: método disponible, banner, vista previa y Glosa."""
        clave = self._clave_recomendacion
        if clave is None or clave[0] != self.square_panel.n:
            self._aplicar_disponibilidad_metodo()
        self._actualizar_recomendacion()
        self._trigger_live_preview()
        self._atenuar_resultado()
        self._refrescar_glosa()

    def _detener_reproductor(self) -> None:
        """Detiene y descarta el reproductor de pasos activo, si existe."""
        if self.reproductor_pasos is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None

    def _preparar_contenedor(self, *, centrado: bool) -> None:
        """Vacía la tarjeta de resultados y ajusta su alineación."""
        self._detener_reproductor()
        contenedor = self.contenedor_resultados
        contenedor.clear()
        contenedor.style("opacity: 1;")
        if centrado:
            contenedor.classes(remove="items-start justify-start", add="items-center justify-center")
        else:
            contenedor.classes(remove="items-center justify-center", add="items-start justify-start")

    def reset_resultados(self) -> None:
        """Restaura el estado inicial de la tarjeta de resultados."""
        if self.contenedor_resultados is None:
            return
        self._preparar_contenedor(centrado=True)
        with self.contenedor_resultados:
            ui.icon("functions", size="4rem").classes("text-placeholder mb-4")
            ui.label("Listo para calcular").classes("text-xl font-bold text-main")
            ui.label(
                "Ingresa una matriz cuadrada y presiona Calcular determinante"
            ).classes("text-sm text-sec mt-2 text-center")

    def _mostrar_cargando(self, n: int) -> None:
        """Muestra el indicador de carga con un aviso si la matriz es grande."""
        self._preparar_contenedor(centrado=True)
        with self.contenedor_resultados:
            ui.spinner(size="3rem").classes("text-accent mb-4")
            mensaje = "Calculando determinante..."
            if n >= CONFIRMAR_N_GRANDE:
                mensaje += " Las matrices grandes pueden tardar."
            ui.label(mensaje).classes("text-sec font-semibold").props('role="status"')

    @staticmethod
    def _pintar_aviso(mensaje: str, clase: str, icono: str) -> None:
        """Dibuja una insignia con icono y mensaje."""
        with ui.row().classes(f"items-center gap-2 px-4 py-2 {clase} mb-4 w-fit").props(
            'role="alert"'
        ):
            ui.icon(icono, size="sm")
            ui.label(mensaje).classes("font-bold")

    async def calcular(self, sender: Any) -> None:
        """Valida la entrada, confirma dimensiones grandes y ejecuta el cálculo.

        Args:
            sender: Botón que disparó el cálculo, para mostrar su estado de carga.
        """
        if self.square_panel.is_strictly_empty():
            self._preparar_contenedor(centrado=False)
            with self.contenedor_resultados:
                self._pintar_aviso(MENSAJE_VACIO, "badge-warning", "warning_amber")
            return
        n = self.square_panel.n
        if n >= CONFIRMAR_N_GRANDE and not await self._confirmar_dimension_grande(n):
            return
        sender.props("loading=true")
        try:
            await self._ejecutar_calculo(n)
        except Exception:
            self._mostrar_error_inesperado()
        finally:
            if not sender.is_deleted:
                sender.props("loading=false")

    async def _confirmar_dimension_grande(self, n: int) -> bool:
        """Pide confirmación antes de calcular una matriz de dimensión grande."""
        with ui.dialog() as dialogo, ui.card().classes("panel-card no-shadow p-6 min-w-[320px]"):
            ui.label("Confirmar cálculo").classes("text-xl font-bold mb-3")
            ui.label(
                f"Una matriz de {n}×{n} puede tardar unos segundos. ¿Quieres continuar?"
            ).classes("text-sm text-sec mb-6")
            with ui.row().classes("w-full justify-end gap-3"):
                ui.button("Cancelar", on_click=lambda: dialogo.submit(False), color=None).classes(
                    "btn-ghost px-4"
                ).props("ripple=false")
                ui.button("Continuar", on_click=lambda: dialogo.submit(True), color=None).classes(
                    "btn-primary px-4"
                ).props("ripple=false")
        return bool(await dialogo)

    async def _ejecutar_calculo(self, n: int) -> None:
        """Calcula en un hilo aparte, pinta el resultado y actualiza historial y Glosa."""
        metodo = self.method_tabs.value
        datos = self.square_panel.get_matrix_data()
        self._mostrar_cargando(n)
        payload = json.dumps({"n": n, "data": datos, "metodo": metodo})
        resultado = await run.io_bound(DeterminantOpsController.process_determinant, payload)
        if self.contenedor_resultados.is_deleted:
            return
        self.last_result = resultado
        self._result_fp = fingerprint({"data": datos, "metodo": metodo})
        self._preparar_contenedor(centrado=False)
        self._render_resultado(resultado)
        self._registrar_historial(resultado, datos, metodo)
        self._marcar_celda_invalida(resultado)
        self._animar_y_enfocar_resultado()
        self._refrescar_glosa()

    def _registrar_historial(self, resultado: dict[str, Any], datos: list[list[str]], metodo: str) -> None:
        """Guarda en el historial los cálculos que terminaron con un determinante."""
        estado = ESTADOS_HISTORIAL.get(resultado.get("status", ""))
        if estado is None:
            return
        n = resultado.get("n", len(datos))
        etiqueta = ETIQUETAS_METODO.get(metodo, metodo)
        self.historial.agregar(
            {"data": datos, "metodo": metodo},
            titulo=f"{n}×{n}",
            estado=estado[0],
            tono=estado[1],
            detalle=f"{etiqueta}, det = {resultado.get('determinante_str')}",
        )

    def _marcar_celda_invalida(self, resultado: dict[str, Any]) -> None:
        """Resalta y enfoca la celda inválida que reportó el controlador."""
        celda = resultado.get("error_cell")
        if celda:
            self.square_panel.flash_cell(*celda)

    @staticmethod
    def _animar_y_enfocar_resultado() -> None:
        """Compone las fórmulas y lleva la vista a la tarjeta de resultados."""
        identificador = json.dumps(ID_RESULTADOS)
        ui.run_javascript("typesetMathWhenReady();")
        ui.run_javascript(
            f"if (window.replayResultAnimation) replayResultAnimation({identificador});"
        )
        ui.run_javascript(
            f"document.getElementById({identificador})?.scrollIntoView("
            "{behavior: (window.scalarisMotionOK && window.scalarisMotionOK()) ? 'smooth' : 'auto', "
            "block: 'start'});"
        )

    def _mostrar_error_inesperado(self) -> None:
        """Registra el fallo y muestra un mensaje accionable en la tarjeta de resultados."""
        logger.error("Error inesperado al calcular el determinante", exc_info=True)
        if self.contenedor_resultados.is_deleted:
            return
        self._preparar_contenedor(centrado=False)
        with self.contenedor_resultados:
            self._pintar_aviso(MENSAJE_ERROR_INESPERADO, "badge-error", "error")
        ui.notify("Error inesperado", type="negative", position="top")

    async def confirmar_limpieza(self) -> None:
        """Pide confirmación antes de vaciar la matriz y los resultados."""
        if self.square_panel.is_empty():
            ui.notify("La matriz ya está vacía", type="warning", position="top")
            return
        with ui.dialog() as dialogo, ui.card().classes("panel-card no-shadow p-6 min-w-[300px]"):
            ui.label("¿Vaciar datos?").classes("text-xl font-bold mb-4")
            ui.label("Se vaciarán la matriz y el resultado.").classes("text-sm text-sec mb-6")
            with ui.row().classes("w-full justify-end gap-3"):
                ui.button("Cancelar", on_click=dialogo.close, color=None).classes(
                    "btn-ghost px-4"
                ).props("ripple=false")
                ui.button(
                    "Limpiar",
                    on_click=lambda: self.ejecutar_animacion_limpieza(dialogo),
                    color=None,
                ).classes("btn-primary px-4").style(
                    "background: var(--error); color: var(--btn-primary-text);"
                ).props("ripple=false")
        dialogo.open()

    async def ejecutar_animacion_limpieza(self, dialogo: ui.dialog) -> None:
        """Cierra el diálogo, anima la limpieza y vacía los datos."""
        dialogo.close()
        try:
            await ui.run_javascript(
                "return window.animateGarbageCollection()",
                timeout=TIMEOUT_ANIMACION_LIMPIEZA_S,
            )
        except Exception:
            logger.debug("La animación de limpieza no se completó", exc_info=True)
        self.limpiar_todo()

    def limpiar_todo(self) -> None:
        """Vacía la matriz y devuelve la tarjeta de resultados a su estado inicial."""
        self.square_panel.clear()
        self.last_result = None
        self._result_fp = None
        self.reset_resultados()
        self._refrescar_glosa()
