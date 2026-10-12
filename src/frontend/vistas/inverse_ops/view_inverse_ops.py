"""Vista principal para la funcionalidad de Matriz Inversa en Scalaris."""
from __future__ import annotations

import itertools
import logging
from nicegui import ui

from src.backend.utils.formatters import format_fraction_str
from src.backend.utils.validators import MatrixValidator
from src.frontend.componentes.ai_panel import AIPanel
from src.frontend.componentes.calculator import CalculatorPanel
from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.componentes.square_matrix_panel import SquareMatrixPanel
from src.frontend.vistas.inverse_ops._config import AI_CONTEXT_MAX_N
from src.frontend.vistas.inverse_ops.history_mixin import InverseOpsHistoryMixin
from src.frontend.vistas.inverse_ops.results_mixin import InverseOpsResultsMixin
from src.frontend.vistas.inverse_ops.steps_mixin import InverseOpsStepsMixin

logger = logging.getLogger(__name__)


class InverseOpsUI(InverseOpsResultsMixin, InverseOpsStepsMixin, InverseOpsHistoryMixin):
    """Controlador de vista modular para el cálculo de la Matriz Inversa."""

    def __init__(self):
        self.square_panel = SquareMatrixPanel()
        self.calculator = CalculatorPanel()

        self.contenedor_resultados: ui.column | None = None
        self.tools_tabs: ui.tabs | None = None
        self.preview_container: ui.column | None = None
        self.preview_task = None
        self.historial: list[dict] = []
        self.historial_container: ui.column | None = None
        self.last_result: dict | None = None

        self.reproductor_pasos = None
        self._uid_counter = itertools.count()

    def build(self, handoff_token: str = ''):
        """Construye la interfaz completa de la vista."""
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('inversa'))

        self.square_panel.inject_scripts()
        self.square_panel.on_data_change = self._on_matrix_change
        self.calculator.inject_scripts()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            self.handoff_slot = ui.column().classes('w-full')
            self._render_header()

            with ui.element('div').classes('layout-split mb-8'):
                self._render_columna_captura()
                self._render_columna_herramientas()

            self.contenedor_resultados = ui.column().classes(
                'w-full panel-card p-6 items-center justify-center min-h-[400px]'
            ).props('id="resultados-inv"')
            self.reset_resultados()

        self.ai_panel.build()
        self._procesar_handoff_inicial(handoff_token)

    def _render_header(self) -> None:
        """Renderiza título y subtítulo de la herramienta."""
        with ui.column().classes('mb-8'):
            ui.label('Matriz inversa').classes('text-2xl font-bold text-main')
            ui.label('Gauss-Jordan sobre [A | I]').classes(
                'fs-small text-sec uppercase'
            ).style('letter-spacing: 0.08em;')

    def _render_columna_captura(self) -> None:
        """Renderiza la cuadrícula de captura y botones de acción."""
        with ui.column().classes('layout-pane'):
            self.square_panel.build_container()
            with ui.row().classes('w-full mt-6 gap-4'):
                ui.button(
                    icon='delete',
                    on_click=self.confirmar_limpieza,
                    color=None,
                ).classes('btn-ghost flex-1 py-3').props(
                    'ripple=false id="btn-limpiar-main" aria-label="Limpiar"'
                ).tooltip('Limpiar')

                ui.button(
                    'Calcular inversa',
                    on_click=lambda e: self.calcular(e.sender),
                    color=None,
                ).classes('btn-primary flex-[2] py-3').props('ripple=false')

    def _render_columna_herramientas(self) -> None:
        """Renderiza pestañas de teclado, vista previa e historial."""
        with ui.column().classes('layout-pane tools-panel'):
            with ui.tabs().classes('neo-tabs w-full').props('dense no-caps') as self.tools_tabs:
                ui.tab('teclado', label='Teclado')
                ui.tab('preview', label='Vista previa')
                ui.tab('history', label='Historial')

            self.tools_tabs.on_value_change(
                lambda e: self._trigger_live_preview() if e.value == 'preview' else None
            )

            with ui.tab_panels(self.tools_tabs, value='teclado').classes(
                'w-full p-0 bg-transparent'
            ).props('animated'):
                with ui.tab_panel('teclado').classes('p-0 mt-4'):
                    self.calculator.build(None)

                with ui.tab_panel('preview').classes('p-6 panel-card mt-4 min-h-[300px] items-center'):
                    ui.label('Vista Previa en Vivo').classes('font-bold text-main mb-4')
                    self.preview_container = ui.column().classes('w-full items-center justify-center')
                    self._trigger_live_preview()

                with ui.tab_panel('history').classes('p-6 panel-card mt-4 min-h-[300px]'):
                    ui.label('Últimas matrices invertidas').classes('font-bold text-main mb-4')
                    self.historial_container = ui.column().classes('w-full')
                    self._render_history()

    def _procesar_handoff_inicial(self, handoff_token: str) -> None:
        """Recupera la matriz desde navegación entrante si existe token."""
        from src.frontend.componentes.handoff import consumir_matriz, renderizar_aviso_handoff, clean_url_handoff
        from src.frontend.constantes import DIMENSION_MAXIMA_INVERSA
        res = consumir_matriz(handoff_token, max_n=DIMENSION_MAXIMA_INVERSA)
        if res is not None:
            with self.handoff_slot:
                n = len(res.data) if res.data else 0
                renderizar_aviso_handoff(res, f"Cargamos A ({n}×{n}) desde {res.source_name}. Presiona Calcular inversa para ver A⁻¹.")
            if res.status == 'ok':
                self.square_panel.set_data(res.data)
            clean_url_handoff()

    def _preparar_resultado_ia(self, n: int) -> dict | None:
        """Serializa el resultado de la inversa para el contexto IA."""
        if not getattr(self, 'last_result', None):
            return None
        st = self.last_result.get("status")
        if st == "SUCCESS":
            inv_obj = self.last_result.get("inverse")
            res_dict = {
                "status": "SUCCESS",
                "determinante": self.last_result.get("determinant_str"),
                "pasos_totales": self.last_result.get("stats", {}).get("total", 0),
            }
            if n <= AI_CONTEXT_MAX_N and inv_obj:
                from src.ai.contexto import describir_matriz
                inv_rows = inv_obj.data if hasattr(inv_obj, 'data') else inv_obj
                formatted_rows = [[format_fraction_str(c) for c in row] for row in inv_rows]
                res_dict["inverse"] = describir_matriz(formatted_rows)
            else:
                res_dict["inverse_omitted"] = True
            return res_dict
        if st == "SINGULAR":
            return {"status": "SINGULAR", "message": "Matriz singular (det = 0)."}
        return {"status": "ERROR"}

    def obtener_contexto_ia(self):
        from src.ai.contexto import ContextoIA, EstadoContexto, describir_matriz, sanear_cadena_usuario, generar_nota_ventana
        from src.ai.huellas import esta_desactualizado
        n = self.square_panel.n
        if self.square_panel.is_empty():
            return ContextoIA(herramienta="inversa", vista="Matriz inversa", etiqueta="Matriz A", entrada={}, estado=EstadoContexto(vacio=True))

        data = self.square_panel.obtener_datos_matriz()
        data_sanitized = [
            [sanear_cadena_usuario(data[i][j] or "", 32) for j in range(n)]
            for i in range(n)
        ]

        desc_a = describir_matriz(data_sanitized)
        ctx = ContextoIA(
            herramienta="inversa",
            vista="Matriz inversa",
            etiqueta=f"A ({n}×{n})",
            entrada={"A": desc_a}
        )
        ctx.nota_ventana = generar_nota_ventana(desc_a)
        ctx.desactualizado = esta_desactualizado({"data": data}, getattr(self, '_result_fp', None))

        if getattr(self, 'last_result', None):
            ctx.resultado = None if ctx.desactualizado else self._preparar_resultado_ia(n)

        return ctx

    def obtener_senales_ia(self):
        from src.frontend.suggestions import Signals, first_invalid_cell
        try:
            state = "none"
            flags = set()
            invalid = None
            
            n = self.square_panel.n
            data = self.square_panel.obtener_datos_matriz()
            items = []
            for i in range(n):
                for j in range(n):
                    items.append((f"A[{i+1},{j+1}]", data[i][j], (i, j)))
            invalid = first_invalid_cell(items)
            
            res = getattr(self, 'last_result', None)
            if res and not getattr(self.obtener_contexto_ia(), 'desactualizado', True):
                st = res.get("status")
                if st == "SUCCESS":
                    state = "success"
                elif st == "SINGULAR":
                    state = "singular"
                else:
                    state = "none"
            return Signals(tool="inversa", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None

    def focus_cell(self, focus: tuple[int, int]):
        if focus and hasattr(self, 'square_panel'):
            self.square_panel.flash_cell(*focus)
