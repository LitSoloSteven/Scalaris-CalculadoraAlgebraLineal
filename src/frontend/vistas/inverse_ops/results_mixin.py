"""Mixin de resolución, comprobaciones y renderizado de resultados para Matriz Inversa."""
from __future__ import annotations

import asyncio
import html
import json
import logging
from nicegui import run, ui

from src.frontend.constantes import DEBOUNCE_VISTA_PREVIA_SEGUNDOS
from src.backend.constants import (
    INVERSE_LATEX_MAX_DIMENSION,
)
from src.backend.utilidades.formateadores import formatear_fraccion_str
from src.backend.utilidades.validadores import ValidadorMatriz
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.vistas.inverse_ops._config import (
    CONFIRM_BIG_N,
    PREVIEW_MAX_N,
)
from src.frontend.componentes.reproductor_pasos.html_tablas import html_tabla_matriz
from src.frontend.vistas.inverse_ops._tarjeta_inversa import (
    generar_latex_vista_previa,
    renderizar_resultado_error,
    renderizar_resultado_exitoso,
    renderizar_resultado_singular,
)

logger = logging.getLogger(__name__)


class InverseOpsResultsMixin:
    """Maneja el preview en vivo, resolución y presentación de la matriz inversa y verificaciones."""

    def _trigger_live_preview(self):
        """Dispara la actualización de la vista previa con debounce."""
        if self.preview_task and not self.preview_task.done():
            self.preview_task.cancel()
        self.preview_task = asyncio.create_task(self._update_preview())

    async def _update_preview(self):
        """Genera y renderiza el preview de la matriz en MathJax."""
        await asyncio.sleep(DEBOUNCE_VISTA_PREVIA_SEGUNDOS)
        if not self.preview_container or self.preview_container.is_deleted:
            return

        try:
            self.preview_container.clear()
            with self.preview_container:
                n = self.square_panel.n
                data = self.square_panel.obtener_datos_matriz()

                if n > PREVIEW_MAX_N:
                    ui.label(f'Vista previa disponible hasta {PREVIEW_MAX_N}×{PREVIEW_MAX_N}.').classes(
                        'text-sec italic text-sm mt-4 text-center'
                    )
                    return

                matrix_a_tex, aug_tex, typeset_ids = generar_latex_vista_previa(data, n)
                ui.html(
                    f'<div id="preview-a" class="math-scroll-container math-label text-lg mb-4 w-full text-center">$$ A = {matrix_a_tex} $$</div>'
                )
                if aug_tex:
                    ui.html(
                        rf'<div id="preview-aug" class="math-scroll-container math-label text-base w-full text-center">$$ [A \mid I] = {aug_tex} $$</div>'
                    )

                ui.run_javascript(f"if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax({json.dumps(typeset_ids)});")
        except Exception as e:
            if not self.preview_container or self.preview_container.is_deleted:
                return
            logger.error("Error al actualizar vista previa de matriz inversa", exc_info=e)
            with self.preview_container:
                ui.label('No se pudo generar la vista previa.').classes(
                    'text-sec italic text-sm mt-4 text-center'
                )

    def reset_resultados(self):
        """Restaura el estado inicial y placeholder de la tarjeta de resultados."""
        if not self.contenedor_resultados:
            return
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-start justify-start',
            add='items-center justify-center',
        )
        with self.contenedor_resultados:
            ui.icon('flip', size='4rem').classes('text-placeholder mb-4')
            ui.label('Listo para invertir').classes('text-xl font-bold text-main')
            ui.label(
                'Ingresa una matriz cuadrada y presiona Calcular inversa'
            ).classes('text-sm text-sec mt-2 text-center')

    def _on_matrix_change(self):
        """Handler reactivo invocado cuando el usuario edita o redimensiona la matriz."""
        self._trigger_live_preview()
        if self.last_result is not None and self.contenedor_resultados:
            self.contenedor_resultados.style('opacity: 0.45;')
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'programar_actualizacion_contexto'):
            p.programar_actualizacion_contexto()

    async def confirmar_limpieza(self):
        """Muestra el diálogo neumórfico para confirmar el vaciado de datos."""
        if self.square_panel.is_empty():
            ui.notify('El sistema ya está vacío', type='warning', position='top')
            return

        with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[300px]'):
            ui.label('¿Vaciar datos?').classes('text-xl font-bold mb-4')
            ui.label('Se animarán y eliminarán los datos.').classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=dialog.close, color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button(
                    'Limpiar',
                    on_click=lambda: self.ejecutar_animacion_limpieza(dialog),
                    color=None,
                ).classes('btn-primary px-4').style('background: var(--error); color: white;').props('ripple=false')
        dialog.open()

    async def ejecutar_animacion_limpieza(self, dialog):
        """Ejecuta la animación de recolección de basura y limpia la matriz."""
        dialog.close()
        try:
            await ui.run_javascript('return window.scalaris && window.scalaris.animarRecoleccionBasura ? window.scalaris.animarRecoleccionBasura() : Promise.resolve()', timeout=2.0)
        except Exception:
            pass
        self.limpiar_todo()

    def limpiar_todo(self):
        """Limpia los inputs de la matriz y el panel de resultados."""
        self.square_panel.clear()
        self.last_result = None
        self.reset_resultados()

    def _mostrar_aviso_matriz_vacia(self) -> None:
        """Notifica que la matriz está vacía antes de calcular."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-warning mb-4 w-fit'):
                ui.icon('warning', size='sm')
                ui.label('Ingresa al menos un valor antes de calcular.').classes('font-bold')

    async def _confirmar_calculo_grande(self, n: int) -> bool:
        """Muestra diálogo de confirmación si la dimensión es grande."""
        with ui.dialog() as dialog, ui.card().classes('panel-card no-shadow p-6 min-w-[320px]'):
            ui.label('Confirmar cálculo').classes('text-xl font-bold mb-3')
            ui.label(
                f'Una dimensión n={n} ({n}×{n}) puede tardar unos segundos y consumir bastante memoria. '
                f'¿Deseas continuar?'
            ).classes('text-sm text-sec mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancelar', on_click=lambda: dialog.submit(False), color=None).classes('btn-ghost px-4').props('ripple=false')
                ui.button('Continuar', on_click=lambda: dialog.submit(True), color=None).classes('btn-primary px-4').props('ripple=false')
        return bool(await dialog)

    def _mostrar_spinner_calculo(self, n: int) -> None:
        """Renderiza el estado de carga y mensaje explicativo según n."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.style('opacity: 1;')
        self.contenedor_resultados.classes(
            remove='items-start justify-start', add='items-center justify-center'
        )
        with self.contenedor_resultados:
            ui.spinner(size='3rem').classes('text-accent mb-4')
            msg_calc = 'Calculando inversa...'
            if n >= 20:
                msg_calc += ' (matrices grandes pueden tardar)'
            ui.label(msg_calc).classes('text-sec font-semibold')

    def _finalizar_exito_calculo(self, result: dict, n: int) -> None:
        """Actualiza historial, scripts cliente y contexto IA tras cálculo exitoso."""
        if result.get("status") in ("SUCCESS", "SINGULAR"):
            self._add_to_history(
                self.square_panel.obtener_datos_matriz(),
                n,
                result["status"],
                result.get("determinant_str"),
            )

        ui.run_javascript('if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();')
        ui.run_javascript("if(window.scalaris && window.scalaris.reproducirAnimacionResultado) window.scalaris.reproducirAnimacionResultado('resultados-inv');")
        ui.run_javascript(
            "document.getElementById('resultados-inv')?.scrollIntoView({behavior: 'smooth', block: 'start'});"
        )

        from src.ai.huellas import calcular_huella
        self._result_fp = calcular_huella({"data": self.square_panel.obtener_datos_matriz()})
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'programar_actualizacion_contexto'):
            p.programar_actualizacion_contexto()

    async def calcular(self, sender):
        """Punto de entrada para validar, confirmar (si n es grande) y ejecutar el cálculo."""
        if self.square_panel.is_strictly_empty():
            self._mostrar_aviso_matriz_vacia()
            return

        n = self.square_panel.n
        if n >= CONFIRM_BIG_N and not await self._confirmar_calculo_grande(n):
            return

        sender.props('loading=true')
        self._mostrar_spinner_calculo(n)

        try:
            payload = json.dumps({"n": n, "data": self.square_panel.obtener_datos_matriz()})
            result = await run.io_bound(ControladorOperacionesInversas.procesar_inversa, payload)

            if self.contenedor_resultados.is_deleted:
                return

            self.last_result = result
            self.contenedor_resultados.style('opacity: 1;')
            self._render_result(result)
            self._finalizar_exito_calculo(result, n)

        except Exception as e:
            self._mostrar_error_inesperado(e)
        finally:
            if not sender.is_deleted:
                sender.props('loading=false')

    def _mostrar_error_inesperado(self, exc: Exception):
        """Muestra un badge de error ante excepciones no controladas."""
        if self.contenedor_resultados.is_deleted:
            return
        logger.error("Error inesperado en calcular matriz inversa", exc_info=exc)
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )
        with self.contenedor_resultados:
            with ui.row().classes('items-center gap-2 px-4 py-2 badge-error mb-4 w-fit'):
                ui.icon('close', size='sm')
                ui.label(
                    'Ocurrió un error inesperado al procesar la matriz inversa. Revisa los datos e inténtalo de nuevo.'
                ).classes('font-bold')
        ui.notify('Error inesperado', type='negative', position='top')

    def _render_result(self, result: dict):
        """Renderiza la sección de resultados según el estado (ERROR, SINGULAR o SUCCESS)."""
        self.contenedor_resultados.clear()
        self.contenedor_resultados.classes(
            remove='items-center justify-center', add='items-start justify-start'
        )

        status = result.get("status", "ERROR")
        n = result.get("n", self.square_panel.n)

        with self.contenedor_resultados:
            if status == "ERROR":
                renderizar_resultado_error(self, result)
            elif status == "SINGULAR":
                renderizar_resultado_singular(self, result, n)
            else:
                renderizar_resultado_exitoso(self, result, n)

