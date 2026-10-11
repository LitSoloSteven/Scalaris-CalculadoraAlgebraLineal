"""Vista de Transformaciones Lineales T: R^n -> R^m (P5 - LIT-8).

Layout:
  - Panel izquierdo: captura de la matriz A (m×n), nombres de variables
    y 4 presets geometricos (identidad 2D, reflexion, proyeccion, rotacion 90,
    shear, expansion a 3D).
  - Panel derecho: resultados (ker(T), Im(T), rango, nulidad, Teorema de la
    Dimension, callout de convencion de subespacios).
"""
import json
import asyncio
import logging
import html
from functools import partial

from nicegui import ui

logger = logging.getLogger(__name__)

from src.frontend.componentes.app_shell import create_app_shell
from src.frontend.navigation import route_of
from src.frontend.controladores.operaciones_matrices import (
    ControladorTransformaciones,
)
from src.frontend.vistas.matrix_ops._presets_transformaciones import (
    PRESETS_TRANSFORMACIONES,
)
from src.frontend.vistas.matrix_ops._render_transformaciones import (
    renderizar_resultado_transformaciones,
)


class TransformacionesUI:
    """Vista completa de Transformaciones Lineales."""

    def __init__(self):
        self.m = 2  # filas de A (dimension del codominio)
        self.n = 2  # columnas de A (dimension del dominio)
        self.entradas_A: list[list] = []
        self.entradas_vars: list = []
        self.contenedor_A = None
        self.contenedor_vars = None
        self.contenedor_resultados = None
        self.last_result = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self):
        create_app_shell(self, active_route=route_of("transformaciones"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            # Header
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("transform", size="2rem").classes("text-accent")
                with ui.column().classes("gap-0"):
                    ui.label("Transformaciones Lineales").classes("text-2xl font-bold text-main")
                    ui.label("T: R^n -> R^m · Nucleo · Imagen · Rango · Nulidad").classes("text-sm text-sec")

            with ui.element("div").classes("layout-split mb-8"):
                # ── Panel izquierdo ────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self._build_presets()
                    self._build_tamano_selector()
                    self._build_panel_A()
                    self._build_panel_variables()

                    with ui.row().classes("w-full mt-6 gap-4"):
                        ui.button(
                            "Analizar", icon="analytics",
                            on_click=lambda e: self._analizar(e.sender),
                            color=None,
                        ).classes("btn-primary flex-[2] py-3").props("ripple=false")

                # ── Panel derecho ──────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-card p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-transformaciones"')
                    self._reset_resultados()

    # ------------------------------------------------------------------
    # Sub-builders panel izquierdo
    # ------------------------------------------------------------------

    def _build_presets(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Ejemplos geometricos").classes("font-bold text-main mb-2 text-sm uppercase tracking-wide")
            with ui.row().classes("gap-2 flex-wrap"):
                for preset in PRESETS_TRANSFORMACIONES:
                    ui.button(
                        preset["nombre"],
                        on_click=lambda p=preset: self._cargar_preset(p),
                        color=None,
                    ).classes("btn-ghost text-xs py-1 px-3").props("ripple=false").tooltip(preset["descripcion"])

    def _build_tamano_selector(self):
        with ui.row().classes("w-full items-center gap-3 mb-2 flex-wrap"):
            ui.label("Dimensiones A (m×n):").classes("text-sm font-bold text-sec")
            with ui.row().classes("gap-1 items-center"):
                ui.label("m=").classes("text-sm text-sec")
                ui.button(icon="remove", on_click=partial(self._ajustar_m, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Reducir filas m"')
                ui.button(icon="add", on_click=partial(self._ajustar_m, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Aumentar filas m"')
            with ui.row().classes("gap-1 items-center"):
                ui.label("n=").classes("text-sm text-sec")
                ui.button(icon="remove", on_click=partial(self._ajustar_n, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Reducir columnas n"')
                ui.button(icon="add", on_click=partial(self._ajustar_n, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Aumentar columnas n"')

    def _build_panel_A(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Matriz A de la transformacion").classes("font-bold text-main mb-3")
            ui.html(
                '<p class="text-xs text-sec mb-2">'
                "Ingresa la matriz A tal que T(x) = Ax. "
                "Filas m = dimension del codominio R<sup>m</sup>, "
                "columnas n = dimension del dominio R<sup>n</sup>.</p>"
            )
            self.contenedor_A = ui.column().classes("w-full")
            self._generar_cuadricula_A()

    def _build_panel_variables(self):
        with ui.column().classes("w-full panel-card p-4"):
            ui.label("Nombres de variables (opcional)").classes("font-bold text-main mb-2 text-sm")
            self.contenedor_vars = ui.column().classes("w-full")
            self._generar_entradas_vars()

    # ------------------------------------------------------------------
    # Generadores de cuadricula
    # ------------------------------------------------------------------

    def _generar_cuadricula_A(self):
        self.contenedor_A.clear()
        self.entradas_A = []
        with self.contenedor_A:
            for i in range(self.m):
                fila_widgets = []
                with ui.row().classes("gap-1"):
                    for j in range(self.n):
                        inp = ui.input(placeholder="0").classes(
                            "matrix-input w-16 text-center"
                        ).props(f'aria-label="A[{i+1},{j+1}]"')
                        fila_widgets.append(inp)
                self.entradas_A.append(fila_widgets)

    def _generar_entradas_vars(self):
        self.contenedor_vars.clear()
        self.entradas_vars = []
        with self.contenedor_vars:
            with ui.row().classes("gap-2 flex-wrap"):
                for j in range(self.n):
                    inp = ui.input(placeholder=f"x{j+1}", label=f"Var {j+1}").classes(
                        "matrix-input w-16 text-center"
                    ).props(f'aria-label="variable {j+1}"')
                    self.entradas_vars.append(inp)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _ajustar_m(self, delta: int):
        nuevo = self.m + delta
        if not (1 <= nuevo <= 8):
            return
        self.m = nuevo
        self._generar_cuadricula_A()

    def _ajustar_n(self, delta: int):
        nuevo = self.n + delta
        if not (1 <= nuevo <= 8):
            return
        self.n = nuevo
        self._generar_cuadricula_A()
        self._generar_entradas_vars()

    def _cargar_preset(self, preset: dict):
        A = preset["A"]
        nuevo_m = len(A)
        nuevo_n = len(A[0]) if nuevo_m > 0 else 2
        if nuevo_m != self.m or nuevo_n != self.n:
            self.m, self.n = nuevo_m, nuevo_n
            self._generar_cuadricula_A()
            self._generar_entradas_vars()
        for i in range(self.m):
            for j in range(self.n):
                self.entradas_A[i][j].value = A[i][j]
        vars_ = preset.get("variables", [])
        for j, inp in enumerate(self.entradas_vars):
            inp.value = vars_[j] if j < len(vars_) else ""
        ui.notify(f"Preset '{preset['nombre']}' cargado.", type="positive", position="top")

    async def _analizar(self, btn):
        btn.props("loading=true")
        try:
            await asyncio.sleep(0.1)
            await self._analizar_core()
        except Exception as e:
            logger.error("Error inesperado en Transformaciones", exc_info=e)
            self.contenedor_resultados.clear()
            with self.contenedor_resultados:
                with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                    ui.icon("close", size="sm")
                    ui.label("Error inesperado. Revisa los datos e intentalo de nuevo.").classes("font-bold")
        finally:
            btn.props("loading=false")

    async def _analizar_core(self):
        A_raw = []
        for i in range(self.m):
            fila = [self.entradas_A[i][j].value or "0" for j in range(self.n)]
            A_raw.append(fila)

        vars_raw = [inp.value.strip() for inp in self.entradas_vars]
        variables = [v if v else f"x{j+1}" for j, v in enumerate(vars_raw)]

        payload = json.dumps({"A": A_raw, "variables": variables})
        respuesta_str = ControladorTransformaciones.procesar(payload)
        respuesta = json.loads(respuesta_str)
        self.last_result = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove="items-center justify-center", add="items-start justify-start"
            )
            renderizar_resultado_transformaciones(respuesta)

        ui.run_javascript("if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();")
        ui.run_javascript(
            "setTimeout(() => { const el = document.getElementById('resultados-transformaciones'); "
            "if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, 240);"
        )

    def _reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon("transform", size="4rem").classes("text-placeholder mb-4")
            ui.label("Listo para analizar").classes("text-xl font-bold text-main")
            ui.label("Ingresa la matriz A y presiona Analizar.").classes(
                "text-sm text-sec mt-2 text-center"
            )

    # ------------------------------------------------------------------
    # AI context stub
    # ------------------------------------------------------------------

    def obtener_contexto_ia(self):
        return None

    def obtener_senales_ia(self):
        return None
