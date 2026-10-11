"""Vista del Modelo de Insumo-Producto de Leontief (P5 - LIT-8).

Layout:
  - Panel izquierdo: captura de C (n×n) y d (vector de demanda), selector de sectores
    y 3 presets (2 sectores simple, 3 sectores, economía inviable).
  - Panel derecho: resultados del solver (M = I-C, multiplicador, Hawkins-Simon,
    vector de producción x, análisis sectorial).
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
from src.frontend.controladores.operaciones_matrices import ControladorLeontief
from src.frontend.vistas.matrix_ops._presets_leontief import PRESETS_LEONTIEF
from src.frontend.vistas.matrix_ops._render_leontief import (
    renderizar_resultado_leontief,
)


class LeontiefUI:
    """Vista completa del Modelo de Leontief."""

    def __init__(self):
        self.n = 2
        self.entradas_C: list[list] = []   # widgets de entrada de C
        self.entradas_d: list = []          # widgets de entrada de d
        self.entradas_sectores: list = []   # widgets de nombre de sector
        self.contenedor_C = None
        self.contenedor_resultados = None
        self.last_result = None

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self):
        create_app_shell(self, active_route=route_of("leontief"))

        with ui.column().classes("w-full max-w-7xl mx-auto p-6 mt-4 view-root"):
            # Header
            with ui.row().classes("w-full items-center gap-3 mb-6"):
                ui.icon("matriz_inversa", size="2rem").classes("text-accent")
                with ui.column().classes("gap-0"):
                    ui.label("Modelo de Leontief").classes("text-2xl font-bold text-main")
                    ui.label("Insumo-Producto · x = (I - C)^(-1) d").classes("text-sm text-sec")

            with ui.element("div").classes("layout-split mb-8"):
                # ── Panel izquierdo ────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self._build_presets()
                    self._build_tamano_selector()
                    self._build_panel_C()
                    self._build_panel_d()
                    self._build_panel_sectores()

                    with ui.row().classes("w-full mt-6 gap-4"):
                        ui.button(
                            "Calcular", icon="calculate",
                            on_click=lambda e: self._calcular(e.sender),
                            color=None
                        ).classes("btn-primary flex-[2] py-3").props("ripple=false")

                # ── Panel derecho ──────────────────────────────────────
                with ui.column().classes("layout-pane"):
                    self.contenedor_resultados = ui.column().classes(
                        "w-full panel-card p-6 items-center justify-center min-h-[400px]"
                    ).props('id="resultados-leontief"')
                    self._reset_resultados()

    # ------------------------------------------------------------------
    # Sub-builders de panel izquierdo
    # ------------------------------------------------------------------

    def _build_presets(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Ejemplos precargados").classes("font-bold text-main mb-2 text-sm uppercase tracking-wide")
            with ui.row().classes("gap-2 flex-wrap"):
                for preset in PRESETS_LEONTIEF:
                    ui.button(
                        preset["nombre"],
                        on_click=lambda p=preset: self._cargar_preset(p),
                        color=None,
                    ).classes("btn-ghost text-xs py-1 px-3").props("ripple=false").tooltip(preset["descripcion"])

    def _build_tamano_selector(self):
        with ui.row().classes("w-full items-center gap-3 mb-2"):
            ui.label("Tamaño n×n:").classes("text-sm font-bold text-sec")
            ui.button(icon="remove", on_click=partial(self._ajustar_tamano, -1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Reducir dimension"')
            ui.button(icon="add", on_click=partial(self._ajustar_tamano, 1), color=None).classes("btn-neo-icon w-7 h-7 p-0").props('ripple=false aria-label="Aumentar dimension"')

    def _build_panel_C(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Matriz de coeficientes técnicos C").classes("font-bold text-main mb-3")
            ui.html(
                '<p class="text-xs text-sec mb-2">Cada c<sub>ij</sub> indica la fracción de la producción del sector '
                "<i>i</i> que consume el sector <i>j</i> por unidad producida.</p>"
            )
            self.contenedor_C = ui.column().classes("w-full")
            self._generar_cuadricula_C()

    def _build_panel_d(self):
        with ui.column().classes("w-full panel-card p-4 mb-4"):
            ui.label("Vector de demanda final d").classes("font-bold text-main mb-3")
            self.contenedor_d = ui.column().classes("w-full")
            self._generar_entradas_d()

    def _build_panel_sectores(self):
        with ui.column().classes("w-full panel-card p-4"):
            ui.label("Nombres de sectores (opcional)").classes("font-bold text-main mb-3 text-sm")
            self.contenedor_sectores = ui.column().classes("w-full")
            self._generar_entradas_sectores()

    # ------------------------------------------------------------------
    # Generadores de cuadrícula
    # ------------------------------------------------------------------

    def _generar_cuadricula_C(self):
        self.contenedor_C.clear()
        self.entradas_C = []
        with self.contenedor_C:
            for i in range(self.n):
                fila_widgets = []
                with ui.row().classes("gap-1"):
                    for j in range(self.n):
                        inp = ui.input(placeholder="0").classes(
                            "matrix-input w-16 text-center"
                        ).props(f'aria-label="C[{i+1},{j+1}]"')
                        fila_widgets.append(inp)
                self.entradas_C.append(fila_widgets)

    def _generar_entradas_d(self):
        self.contenedor_d.clear()
        self.entradas_d = []
        with self.contenedor_d:
            with ui.row().classes("gap-2 flex-wrap"):
                for i in range(self.n):
                    inp = ui.input(placeholder="0", label=f"d{i+1}").classes(
                        "matrix-input w-20 text-center"
                    ).props(f'aria-label="d[{i+1}]"')
                    self.entradas_d.append(inp)

    def _generar_entradas_sectores(self):
        self.contenedor_sectores.clear()
        self.entradas_sectores = []
        with self.contenedor_sectores:
            with ui.row().classes("gap-2 flex-wrap"):
                for i in range(self.n):
                    inp = ui.input(placeholder=f"Sector {i+1}", label=f"Sector {i+1}").classes(
                        "matrix-input w-28"
                    ).props(f'aria-label="nombre sector {i+1}"')
                    self.entradas_sectores.append(inp)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _ajustar_tamano(self, delta: int):
        nuevo_n = self.n + delta
        if not (2 <= nuevo_n <= 8):
            return
        self.n = nuevo_n
        self._generar_cuadricula_C()
        self._generar_entradas_d()
        self._generar_entradas_sectores()

    def _cargar_preset(self, preset: dict):
        C = preset["C"]
        nuevo_n = len(C)
        if nuevo_n != self.n:
            self.n = nuevo_n
            self._generar_cuadricula_C()
            self._generar_entradas_d()
            self._generar_entradas_sectores()

        for i in range(self.n):
            for j in range(self.n):
                self.entradas_C[i][j].value = C[i][j]
        for i, v in enumerate(preset["d"]):
            self.entradas_d[i].value = v
        sectores = preset.get("sectores", [])
        for i, inp in enumerate(self.entradas_sectores):
            inp.value = sectores[i] if i < len(sectores) else ""
        ui.notify(f"Preset '{preset['nombre']}' cargado.", type="positive", position="top")

    async def _calcular(self, btn):
        btn.props("loading=true")
        try:
            await asyncio.sleep(0.1)
            await self._calcular_core()
        except Exception as e:
            logger.error("Error inesperado en Leontief", exc_info=e)
            self.contenedor_resultados.clear()
            with self.contenedor_resultados:
                with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit"):
                    ui.icon("close", size="sm")
                    ui.label("Error inesperado. Revisa los datos e inténtalo de nuevo.").classes("font-bold")
        finally:
            btn.props("loading=false")

    async def _calcular_core(self):
        # Recoger C
        C_raw = []
        for i in range(self.n):
            fila = []
            for j in range(self.n):
                fila.append(self.entradas_C[i][j].value or "0")
            C_raw.append(fila)

        d_raw = [inp.value or "0" for inp in self.entradas_d]
        sectores_raw = [inp.value.strip() for inp in self.entradas_sectores]
        sectores = [s if s else f"Sector {i+1}" for i, s in enumerate(sectores_raw)]

        payload = json.dumps({"C": C_raw, "d": d_raw, "sectores": sectores})
        respuesta_str = ControladorLeontief.procesar(payload)
        respuesta = json.loads(respuesta_str)
        self.last_result = respuesta

        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            self.contenedor_resultados.classes(
                remove="items-center justify-center", add="items-start justify-start"
            )
            renderizar_resultado_leontief(respuesta)

        ui.run_javascript("if(window.scalaris && window.scalaris.renderizarMathJax) window.scalaris.renderizarMathJax();")
        ui.run_javascript(
            "setTimeout(() => { const el = document.getElementById('resultados-leontief'); "
            "if(el) el.scrollIntoView({behavior: 'smooth', block: 'start'}) }, 240);"
        )

    def _reset_resultados(self):
        self.contenedor_resultados.clear()
        with self.contenedor_resultados:
            ui.icon("matriz_inversa", size="4rem").classes("text-placeholder mb-4")
            ui.label("Listo para calcular").classes("text-xl font-bold text-main")
            ui.label("Ingresa la matriz C y el vector d, luego presiona Calcular.").classes(
                "text-sm text-sec mt-2 text-center"
            )

    # ------------------------------------------------------------------
    # AI context stub (requerido por create_app_shell si usa ai_panel)
    # ------------------------------------------------------------------

    def obtener_contexto_ia(self):
        return None

    def obtener_senales_ia(self):
        return None
