"""Vista principal de Operaciones con Vectores en Scalaris."""
import json
import asyncio
import logging
from nicegui import ui

logger = logging.getLogger(__name__)
from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.componentes.ai_panel import AIPanel
from src.frontend.componentes.vector_capture import VectorCapturePanel
from src.frontend.controladores.operaciones_vectores import (
    ControladorOperacionesVectores,
)
from .results_mixin import VectorOpsResultsMixin

class VectorOpsUI(VectorOpsResultsMixin):
    """Controlador de vista modular para operaciones con vectores."""

    def __init__(self):
        self.active_op = 'add_sub'
        self.ai_panel = None
        self.right_panel = None
        self.current_result = None
        self.btn_calculate = None

        # 1. Suma / Resta
        self.panel_add_sub = VectorCapturePanel(
            panel_id="p_add", min_vectors=2, max_vectors=2
        )
        # 2. Escalar x Vector
        self.panel_scalar = VectorCapturePanel(
            panel_id="p_scal", min_vectors=1, max_vectors=1
        )
        # 3. Combinación Lineal
        self.panel_lin_comb = VectorCapturePanel(
            panel_id="p_lin", min_vectors=2, max_vectors=9,
            allow_orientation_toggle=False, default_orientation='column',
            first_vector_fixed_label="b"
        )

        self.panels = {
            'add_sub': self.panel_add_sub,
            'scalar': self.panel_scalar,
            'lin_comb': self.panel_lin_comb
        }
        self.panel_add_sub.on_data_change = self._on_vectors_change
        self.panel_scalar.on_data_change = self._on_vectors_change
        self.panel_lin_comb.on_data_change = self._on_vectors_change

        # Estado de pestañas específicas
        self.add_sub_operation = 'add'
        self.add_sub_strict = False
        self.scalar_value = "2"

    def _on_vectors_change(self):
        p = getattr(self, 'ai_panel', None)
        if p and hasattr(p, 'programar_actualizacion_contexto'):
            p.programar_actualizacion_contexto()

    @property
    def vector_panel(self):
        return self.panels[self.active_op]

    def _render_panel_suma_resta(self) -> None:
        """Renderiza controles específicos de suma y resta de vectores."""
        with ui.row().classes('w-full justify-between items-center mb-4 panel-card p-4'):
            with ui.row().classes('gap-4 items-center'):
                ui.label('Operación:').classes('font-bold')
                self.op_select = ui.select(
                    {'add': 'Suma', 'subtract': 'Resta'},
                    value=self.add_sub_operation,
                    on_change=lambda e: (setattr(self, 'add_sub_operation', e.value), self._on_vectors_change())
                ).classes('neo-select w-44').props('popup-content-class="neo-select-menu"')
            self.strict_check = ui.checkbox(
                'Estricto (No auto-transponer)',
                value=self.add_sub_strict,
                on_change=lambda e: (setattr(self, 'add_sub_strict', e.value), self._on_vectors_change())
            ).classes('neo-checkbox')
        self.panel_add_sub.build_container()

    def _render_panel_escalar(self) -> None:
        """Renderiza controles para multiplicación de escalar por vector."""
        with ui.row().classes('w-full items-center mb-4 panel-card p-4 gap-4'):
            ui.label('Escalar (k):').classes('font-bold')
            self.scalar_input = ui.input(
                value=self.scalar_value,
                on_change=lambda e: (setattr(self, 'scalar_value', e.value), self._on_vectors_change())
            ).classes('w-32 matrix-input').props('borderless')
        self.panel_scalar.build_container()

    def _render_panel_izquierdo(self) -> None:
        """Renderiza tabs, páneles de captura y barra de acciones."""
        with ui.column().classes('layout-pane p-8 bg-[var(--bg-page)]').style('scroll-behavior: smooth;') as self.left_panel:
            with ui.row().classes('w-full justify-between items-center mb-8 gap-4 flex-wrap'):
                with ui.tabs().classes('neo-tabs method-tabs').props('dense no-caps mobile-arrows').style('max-width: 560px !important') as self.method_tabs:
                    ui.tab('add_sub', label='Suma / Resta')
                    ui.tab('scalar', label='Escalar × Vector')
                    ui.tab('lin_comb', label='Combinación Lineal')
                self.method_tabs.value = self.active_op
                self.method_tabs.on_value_change(self.on_tab_change)

            with ui.tab_panels(self.method_tabs, value=self.active_op).classes('w-full bg-transparent p-0').style('flex: 1;'):
                with ui.tab_panel('add_sub').classes('p-0'):
                    self._render_panel_suma_resta()
                with ui.tab_panel('scalar').classes('p-0'):
                    self._render_panel_escalar()
                with ui.tab_panel('lin_comb').classes('p-0'):
                    ui.markdown('Evalúa si el vector **b** es combinación lineal de los demás vectores.').classes('mb-4 text-sec text-sm')
                    self.panel_lin_comb.build_container()

            with ui.row().classes('w-full justify-between mt-8 pt-4 border-t border-[var(--border-input)] items-center'):
                ui.button('Limpiar', icon='delete', on_click=self.clear_all, color=None).classes('btn-ghost').props('ripple=false id="btn-limpiar-main"')
                self.btn_calculate = ui.button('Calcular', icon='calculate', on_click=self.calculate, color=None).classes('btn-primary px-8 py-2 font-bold')

    def build(self):
        """Construye la interfaz completa de la vista de operaciones con vectores."""
        self.ai_panel = AIPanel(self)
        create_app_shell(self, active_route=route_of('vectores'))
        ui.add_head_html('<script>if(window.scalaris && window.scalaris.renderizarMathJax){window.scalaris.renderizarMathJax();}</script>')
        self.panel_add_sub.inject_scripts()

        with ui.column().classes('w-full max-w-7xl mx-auto p-6 mt-4 view-root'):
            with ui.element('div').classes('layout-split mb-8'):
                self._render_panel_izquierdo()
                with ui.column().classes('layout-pane p-8 bg-[var(--bg-page)]') as self.right_panel:
                    self.render_empty_state()

        self.ai_panel.build()

    def _ejecutar_calculo_segun_operacion(self, vecs_dict: dict) -> str | None:
        """Despacha la operación activa al controlador de operaciones con vectores."""
        v_keys = list(vecs_dict.keys())
        if self.active_op == 'add_sub':
            payload = {
                "operation": self.add_sub_operation,
                "v1": vecs_dict[v_keys[0]],
                "v2": vecs_dict[v_keys[1]],
                "strict": self.add_sub_strict,
            }
            return ControladorOperacionesVectores.procesar_suma_resta(json.dumps(payload))

        if self.active_op == 'scalar':
            payload = {"scalar": self.scalar_input.value, "v": vecs_dict[v_keys[0]]}
            return ControladorOperacionesVectores.procesar_multiplicacion_escalar(json.dumps(payload))

        if self.active_op == 'lin_comb':
            b_key = self.panel_lin_comb.first_vector_fixed_label
            b_vec = vecs_dict.pop(b_key, None)
            if not b_vec:
                ui.notify("No se encontró el vector b.", type='negative')
                return None
            payload = {"b": b_vec, "vectors": list(vecs_dict.values())}
            return ControladorOperacionesVectores.procesar_combinacion_lineal(json.dumps(payload))
        return None

    def _finalizar_calculo_exitoso(self, res: dict) -> None:
        """Renderiza resultado, refresca fingerprint y sincroniza MathJax."""
        self.current_result = res
        self.render_result(res)

        from src.ai.context import fingerprint
        entrada = {
            "op": self.active_op,
            "vectors": {k: dict(v.get('cache', {})) for k, v in self.vector_panel.vectors.items()},
            "scalar": self.scalar_value,
            "add_sub_op": self.add_sub_operation,
            "strict": self.add_sub_strict,
        }
        self._result_fp = fingerprint(entrada)
        self._on_vectors_change()
        ui.run_javascript("setTimeout(() => { if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax(); }, 100);")

    async def calculate(self):
        """Valida entradas y resuelve la operación vectorial seleccionada."""
        self.btn_calculate.disable()
        self.btn_calculate.props('loading')
        try:
            try:
                vecs_dict = self.vector_panel.get_vectors_dict()
            except ValueError as e:
                ui.notify(str(e), type='negative')
                return

            res_str = self._ejecutar_calculo_segun_operacion(vecs_dict)
            if res_str is None:
                return

            res = json.loads(res_str)
            self._finalizar_calculo_exitoso(res)
        except Exception:
            logger.exception("Error inesperado al calcular operaciones con vectores")
            ui.notify("Ocurrió un error inesperado al procesar el cálculo. Inténtalo de nuevo.", type='negative')
        finally:
            self.btn_calculate.enable()
            self.btn_calculate.props(remove='loading')

    def _extraer_datos_vectores_ia(self, vecs: dict) -> dict:
        """Construye descripciones serializadas de vectores para IA."""
        from src.ai.context import describir_matriz, sanitize_user_string
        input_data = {}
        for k, v in vecs.items():
            if "data" in v:
                sanitized_data = [[sanitize_user_string(str(x), 32)] for x in v["data"]]
                input_data[k] = describir_matriz(sanitized_data)
                input_data[k]["orientation"] = v.get("orientation", "column")
        return input_data

    def obtener_contexto_ia(self):
        """Genera el AIContext con la entrada vectorial actual y estado stale."""
        from src.ai.context import AIContext, is_stale
        try:
            vecs = self.vector_panel.get_vectors_dict()
        except Exception:
            vecs = {}

        if not vecs:
            return AIContext("vector_ops", "Vectores", "Operaciones Vectoriales", {}, empty=True)

        ctx = AIContext("vector_ops", "Vectores", f"Operación: {self.active_op}", self._extraer_datos_vectores_ia(vecs))
        entrada_actual = {
            "op": self.active_op,
            "vectors": {k: dict(v.get('cache', {})) for k, v in self.vector_panel.vectors.items()},
            "scalar": self.scalar_value, "add_sub_op": self.add_sub_operation, "strict": self.add_sub_strict,
        }
        ctx.stale = is_stale(entrada_actual, getattr(self, '_result_fp', None))

        if getattr(self, 'current_result', None):
            if ctx.stale:
                ctx.result = None
            else:
                res = self.current_result
                ctx.result = {"status": res.get("status", "ERROR"), "message": res.get("message", "")}
                if res.get("result_vector"):
                    ctx.result["result_vector"] = res["result_vector"]
                if res.get("is_linear_combination") is not None:
                    ctx.result["is_linear_combination"] = res["is_linear_combination"]

        return ctx

    def focus_cell(self, focus):
        if hasattr(self.vector_panel, 'flash_cell'):
            self.vector_panel.flash_cell(focus[0], focus[1])

    def obtener_senales_ia(self):
        from src.frontend.suggestions import Signals, first_invalid_cell
        try:
            state = "none"
            flags = set()
            invalid = None
            
            orients = set()
            items = []
            for idx, (name, vec) in enumerate(self.vector_panel.vectors.items()):
                orients.add(vec['orientation'])
                for r in range(self.vector_panel.dim):
                    val = vec['cache'].get(r, '')
                    items.append((f"{name}[{r+1}]", val, (idx, r)))
            invalid = first_invalid_cell(items)
                
            if 'row' in orients and 'column' in orients:
                flags.add("orient_mix")
                
            if self.active_op == 'scalar' and self.scalar_value.strip().startswith('-'):
                flags.add("neg_scalar")
                
            res = getattr(self, 'current_result', None)
            if res and not getattr(self.obtener_contexto_ia(), 'stale', True):
                st = res.get("status")
                if st == "UNIQUE": state = "unique"
                elif st == "INFINITE": state = "infinite"
                elif st == "NO_SOLUTION": state = "no_solution"
                
            return Signals(tool="vectores", state=state, flags=frozenset(flags), invalid=invalid)
        except Exception:
            return None
