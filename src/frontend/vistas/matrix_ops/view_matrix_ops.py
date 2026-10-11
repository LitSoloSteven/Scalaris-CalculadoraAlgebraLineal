"""Vista interactiva para evaluación de expresiones matriciales en Scalaris."""

from __future__ import annotations

import logging

from nicegui import ui

from src.frontend.componentes.ai_panel import AIPanel
from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.componentes.matrix_capture import MatrixCapturePanel
from src.frontend.navigation import route_of
from src.frontend.vistas.matrix_ops.results_mixin import MatrixOpsResultsMixin

logger = logging.getLogger(__name__)


class MatrixOpsUI(MatrixOpsResultsMixin):
    """Controlador de vista modular para el cálculo y paso a paso de matrices."""

    def __init__(self):
        self.capture_panel = MatrixCapturePanel()
        self.contenedor_resultados = None
        self.input_expresion = None
        self.reproductor_pasos = None

    def reset_resultados(self):
        """Limpia los resultados y detiene cualquier reproducción activa."""
        if getattr(self, 'reproductor_pasos', None) is not None:
            self.reproductor_pasos.detener()
            self.reproductor_pasos = None

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon('data_object', size='4rem').classes('text-placeholder mb-4')
            ui.label('Sin resultados').classes('text-xl font-bold text-main')
            ui.label(
                'Añade matrices y escribe una expresión matemática para empezar'
            ).classes('text-sm text-sec mt-2 text-center')

    def _on_matrix_change(self):
        """Notifica al panel de Glosa cuando cambian los datos de las matrices."""
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'programar_actualizacion_contexto'):
            p.programar_actualizacion_contexto()

    def _navegar_a_inversa(self, name: str, mat: dict) -> None:
        """Valida y redirige a la vista de matriz inversa mediante handoff."""
        if mat['m'] != mat['n']:
            ui.notify(f"La matriz {name} debe ser cuadrada para invertirla.", type='warning')
            return
        if mat['m'] > 10:
            ui.notify(
                f"La herramienta de inversa admite hasta 10x10. La matriz {name} es de {mat['m']}x{mat['n']}.",
                type='warning',
            )
            return

        data = []
        for r in range(mat['m']):
            row = [str(mat['cache'].get((r, c), '0')).strip() or '0' for c in range(mat['n'])]
            data.append(row)

        from src.frontend.componentes.handoff import url_handoff, guardar_matriz
        from src.frontend.navigation import route_of
        token = guardar_matriz('matrices', data)
        ui.navigate.to(url_handoff(route_of('inversa'), token))

    def _render_panel_expresion(self) -> None:
        """Renderiza el input de la expresión matemática y el botón Evaluar."""
        with ui.column().classes('w-full panel-card p-6 mt-4'):
            ui.label('Expresión Matemática').classes('text-lg font-bold text-main mb-2')
            self.input_expresion = ui.input(
                placeholder='Ej. A + B * C'
            ).classes('matrix-input w-full text-xl py-2').props(
                'borderless autocomplete="new-password"'
            )
            self.input_expresion.on_value_change(lambda _: self._on_matrix_change())

            ui.button(
                'Evaluar',
                icon='calculate',
                on_click=lambda e: self.evaluar_expresion(e.sender),
                color=None,
            ).classes('btn-primary w-full py-3 mt-4').props('ripple=false')

    def build(self):
        """Construye los paneles de captura, expresión y resultados."""
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('matrices'))
        self.capture_panel.inject_scripts()
        self.capture_panel.on_data_change = self._on_matrix_change

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                ui.label('Matrices').classes('text-2xl font-bold text-main')

            with ui.element('div').classes('layout-split mb-8'):
                with ui.column().classes('layout-pane'):
                    self.capture_panel.build_container()
                    self.capture_panel.on_invert = self._navegar_a_inversa
                    self._render_panel_expresion()

                with ui.column().classes('layout-pane'):
                    self.contenedor_resultados = ui.column().classes(
                        'w-full panel-card p-6 items-center justify-center min-h-[400px]'
                    ).props('id="resultados-ops"')
                    self.reset_resultados()

        self.ai_panel.build()

    def _extraer_datos_matrices_ia(self, mats: dict) -> tuple[dict, list]:
        """Extrae matrices sanitizadas y descripciones de texto para IA."""
        from src.ai.context import describir_matriz, sanitize_user_string
        input_data = {}
        descs = []
        for k, v in mats.items():
            if "data" in v:
                sanitized = [[sanitize_user_string(c, 32) for c in r] for r in v["data"]]
                d = describir_matriz(sanitized)
                input_data[k] = d
                descs.append(d)
        return input_data, descs

    def obtener_contexto_ia(self):
        """Proporciona el contexto serializado al asistente Glosa."""
        from src.ai.context import AIContext, is_stale, sanitize_user_string, window_note_from
        try:
            mats = self.capture_panel.obtener_diccionario_matrices()
        except Exception:
            mats = {}

        expr_val = self.input_expresion.value if hasattr(self, 'input_expresion') and self.input_expresion else ""
        if not mats and not expr_val:
            return AIContext("matrix_ops", "Matrices", "Operaciones", {}, empty=True)

        input_data, descs = self._extraer_datos_matrices_ia(mats)
        if expr_val:
            input_data["expresion"] = sanitize_user_string(expr_val, 200)

        ctx = AIContext("matrix_ops", "Matrices", "Matrices y Expresión", input_data)
        ctx.window_note = window_note_from(*descs)

        entrada_actual = {
            "matrices": {name: dict(m.get('cache', {})) for name, m in self.capture_panel.matrices.items()},
            "expresion": (expr_val or "").strip(),
        }
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))

        if getattr(self, 'last_result', None):
            if ctx.stale:
                ctx.result = None
            else:
                res = self.last_result
                ctx.result = {"status": res.get("status", "ERROR"), "message": res.get("message", "")}
                if res.get("final_variable"):
                    ctx.result["final_variable"] = res["final_variable"]

        return ctx

    def _evaluar_estado_resultado(self, res: dict, expr: str, flags: set) -> str:
        """Determina el estado (ok, error, dim_error) y banderas a partir del resultado."""
        import re
        st = res.get("status")
        if st == "SUCCESS":
            if re.search(r'[A-Z)]\s*\*?\s*[A-Z(]', expr):
                flags.add("has_product")
            return "ok"
        if st == "ERROR":
            msg = res.get("message", "").lower()
            return "dim_error" if ("dimensi" in msg or "tamaño" in msg) else "error"
        return "none"

    def obtener_senales_ia(self):
        """Calcula señales heurísticas para sugerencias proactivas."""
        from src.frontend.suggestions import Signals, first_invalid_cell
        try:
            state = "none"
            flags = set()
            expr = (
                self.input_expresion.value.strip()
                if hasattr(self, 'input_expresion') and self.input_expresion and self.input_expresion.value
                else ""
            )

            has_nonzero = False
            items = []
            for name, m in self.capture_panel.matrices.items():
                for (r, c), val in m.get('cache', {}).items():
                    val_str = str(val).strip()
                    if val_str and val_str not in ('0', '0.0'):
                        has_nonzero = True
                    items.append((f"{name}[{r+1},{c+1}]", val))

            if not has_nonzero and not expr:
                state = "empty"

            invalid = first_invalid_cell(items)
            res = getattr(self, 'last_result', None)
            if res and not getattr(self.obtener_contexto_ia(), 'stale', True):
                state = self._evaluar_estado_resultado(res, expr, flags)

            return Signals(tool="matrices", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None
