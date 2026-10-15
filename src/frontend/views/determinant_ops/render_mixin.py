"""Presentación del resultado del cálculo de determinantes."""
from __future__ import annotations

import html
import json
from fractions import Fraction
from typing import Any

from nicegui import ui

from src.backend.models.matrix import Matrix
from src.backend.utils.formatters import format_fraction_str
from src.frontend.components.handoff import handoff_url, put_matrix
from src.frontend.components.reproductor_pasos import (
    formatear_decimal,
    html_tabla_matriz,
    render_latex,
)
from src.frontend.controllers.determinant_ops._config import ETIQUETAS_METODO
from src.frontend.navigation import route_of
from src.frontend.views.determinant_ops.metodo_mixin import METODO_LU

OPACIDAD_RESULTADO_OBSOLETO = 0.45
VELOCIDAD_ESCRITURA_MS = 20
FUENTE_HANDOFF = "determinantes"
LIMITE_DECIMAL_MINIMO = 1e-4
LIMITE_DECIMAL_MAXIMO = 1e9
CIFRAS_NOTACION = 4
TEXTO_INVERTIBLE = "det(A) ≠ 0: la matriz es invertible"
TEXTO_SINGULAR = "det(A) = 0: la matriz es singular"
MENSAJE_ERROR_GENERICO = "No se pudo calcular el determinante. Revisa los datos e inténtalo de nuevo."
TEXTO_INTERPRETACION = (
    "Si det(A) ≠ 0, la matriz tiene inversa y sus columnas son linealmente independientes. "
    "Si det(A) = 0 ocurre lo contrario. Cada intercambio de filas cambia el signo del "
    "determinante. En una matriz triangular, el determinante es el producto de su diagonal."
)
PROPS_EXPANSION = 'header-class="font-bold text-main"'


def _js_escribir_insignia(identificador: str, texto: str) -> str:
    """Genera el JS que anima la insignia solo si el movimiento está permitido."""
    return (
        f"if (window.scalarisMotionOK && window.scalarisMotionOK()) "
        f"window.typewriterEffect({json.dumps(identificador)}, {json.dumps(texto)}, "
        f"{VELOCIDAD_ESCRITURA_MS});"
    )


def _etiqueta_decimal(valor: Fraction) -> str:
    """Redacta la aproximación decimal de det(A) sin confundir un valor pequeño con 0."""
    if valor == 0:
        return "det(A) = 0"
    try:
        aproximado = float(valor)
    except OverflowError:
        return "det(A) es demasiado grande para mostrarlo en decimales"
    magnitud = abs(aproximado)
    if magnitud == 0.0:
        return "det(A) no es 0, pero es demasiado pequeño para mostrarlo en decimales"
    if LIMITE_DECIMAL_MINIMO <= magnitud < LIMITE_DECIMAL_MAXIMO:
        return f"det(A) ≈ {formatear_decimal(valor)}"
    return f"det(A) ≈ {aproximado:.{CIFRAS_NOTACION}e}"


def _pintar_error(resultado: dict[str, Any]) -> None:
    """Muestra el mensaje de error; la celda inválida ya fue marcada por el cálculo."""
    with ui.row().classes("items-center gap-2 px-4 py-2 badge-error mb-4 w-fit").props(
        'role="alert"'
    ):
        ui.icon("error", size="sm")
        ui.label(resultado.get("message") or MENSAJE_ERROR_GENERICO).classes("font-bold")


def _pintar_formula(resultado: dict[str, Any]) -> None:
    """Dibuja det(A) como igualdad en LaTeX o, si A es grande, como tabla."""
    latex_a = resultado.get("matrix_a_latex")
    if latex_a:
        render_latex(rf"\det(A) = {latex_a} = {resultado['determinante_latex']}")
    elif resultado.get("matrix_a") is not None:
        ui.html(html_tabla_matriz(resultado["matrix_a"]))


def _copiar_al_portapapeles(texto: str) -> None:
    """Copia det(A) al portapapeles y confirma con un aviso."""
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(texto)});")
    ui.notify("det(A) copiado al portapapeles", type="positive")


def _ir_a_inversa(matriz: Matrix) -> None:
    """Lleva A a Matriz inversa mediante el traspaso compartido de datos."""
    datos = [
        [format_fraction_str(matriz.get(i, j)) for j in range(matriz.cols)]
        for i in range(matriz.rows)
    ]
    token = put_matrix(FUENTE_HANDOFF, datos)
    ui.navigate.to(handoff_url(route_of("inversa"), token))


def _pintar_acciones(resultado: dict[str, Any]) -> None:
    """Dibuja los botones de copiar y de abrir A⁻¹ en Matriz inversa."""
    matriz = resultado.get("matrix_a")
    texto = str(resultado["determinante_str"])
    with ui.row().classes("w-full gap-2 mt-4 flex-wrap"):
        ui.button(
            "Copiar det(A)",
            icon="content_copy",
            on_click=lambda: _copiar_al_portapapeles(texto),
            color=None,
        ).classes("btn-ghost text-xs").props("ripple=false")
        if not resultado.get("es_singular") and matriz is not None:
            ui.button(
                "Ver A⁻¹ en Matriz inversa",
                on_click=lambda: _ir_a_inversa(matriz),
                color=None,
            ).classes("btn-ghost text-xs").props("ripple=false")


def _pintar_decimal(resultado: dict[str, Any]) -> None:
    """Muestra una aproximación decimal del determinante exacto."""
    with ui.expansion("Ver det(A) en decimales (≈4 cifras)", icon="numbers").classes(
        "w-full mt-3 panel-card"
    ).props('header-class="font-bold text-main text-sm"'):
        ui.label(_etiqueta_decimal(resultado["determinante"])).classes("det-leyenda p-3")


def _pintar_verificacion(verificacion: dict[str, Any]) -> None:
    """Dibuja una comprobación con su insignia textual y su detalle LaTeX."""
    correcto = bool(verificacion.get("coincide"))
    with ui.row().classes("w-full justify-between items-center gap-4 flex-wrap"):
        ui.label(str(verificacion.get("title", ""))).classes("font-bold text-main text-sm")
        ui.badge("Correcto" if correcto else "Incorrecto", color=None).classes(
            "badge-success" if correcto else "badge-error"
        )
    detalle = verificacion.get("detail_latex")
    if detalle:
        render_latex(detalle)


def _pintar_comprobaciones(resultado: dict[str, Any]) -> None:
    """Dibuja la expansión con todas las comprobaciones formales del cálculo."""
    with ui.expansion("Comprobaciones formales", icon="verified").classes(
        "w-full mb-6 panel-card"
    ).props(f"default-opened {PROPS_EXPANSION}"):
        with ui.column().classes("w-full gap-4 p-2"):
            for verificacion in resultado.get("verifications") or []:
                _pintar_verificacion(verificacion)


def _pintar_interpretacion() -> None:
    """Dibuja la ayuda breve para interpretar el determinante."""
    with ui.expansion("¿Cómo interpretar este resultado?", icon="help_outline").classes(
        "w-full mt-6 panel-card"
    ).props(PROPS_EXPANSION):
        ui.label(TEXTO_INTERPRETACION).classes("text-sec text-sm p-3")


class DeterminantOpsRenderMixin:
    """Pinta el resultado del determinante en el contenedor de resultados.

    Requiere en la vista: contenedor_resultados, square_panel, last_result, ai_panel y
    _uid_counter, además de _render_steps_section del mixin de pasos.
    """

    def _atenuar_resultado(self) -> None:
        """Atenúa el resultado previo cuando los datos de entrada ya no lo respaldan."""
        if self.last_result is not None and self.contenedor_resultados is not None:
            self.contenedor_resultados.style(f"opacity: {OPACIDAD_RESULTADO_OBSOLETO};")

    def _render_resultado(self, resultado: dict[str, Any]) -> None:
        """Renderiza el estado ERROR, SINGULAR o SUCCESS del cálculo.

        Args:
            resultado: Diccionario devuelto por el controlador de determinantes.
        """
        contenedor = self.contenedor_resultados
        contenedor.clear()
        contenedor.style("opacity: 1;")
        contenedor.classes(remove="items-center justify-center", add="items-start justify-start")
        with contenedor:
            if resultado.get("status", "ERROR") == "ERROR":
                _pintar_error(resultado)
                return
            self._pintar_insignia(resultado)
            self._pintar_resumen(resultado)
            self._pintar_tarjeta_resultado(resultado)
            _pintar_comprobaciones(resultado)
            self._render_steps_section(resultado)
            _pintar_interpretacion()

    def _pintar_insignia(self, resultado: dict[str, Any]) -> None:
        """Dibuja la insignia de invertible o singular con escritura animada."""
        singular = resultado.get("status") == "SINGULAR"
        texto = TEXTO_SINGULAR if singular else TEXTO_INVERTIBLE
        identificador = f"badge-det-{next(self._uid_counter)}"
        clase = "badge-warning" if singular else "badge-success"
        escapado = html.escape(texto)
        with ui.row().classes(f"items-center gap-2 px-4 py-2 {clase} mb-4 w-fit").props(
            'role="status"'
        ):
            ui.icon("warning_amber" if singular else "check_circle", size="sm")
            # La copia oculta evita que el lector anuncie la escritura letra por letra.
            ui.html(
                f'<span aria-hidden="true" id="{identificador}">{escapado}</span>'
                f'<span class="det-solo-lectores">{escapado}</span>'
            ).classes("font-bold")
        ui.run_javascript(_js_escribir_insignia(identificador, texto))

    def _pintar_resumen(self, resultado: dict[str, Any]) -> None:
        """Dibuja la fila de datos del cálculo y los chips de sugerencia de Glosa."""
        n = resultado.get("n", self.square_panel.n)
        metodo = resultado.get("metodo", "")
        total = (resultado.get("stats") or {}).get("total", len(resultado.get("steps") or []))
        tiempo = f"{resultado.get('elapsed_s', 0.0):.2f}".replace(".", ",")
        with ui.row().classes(
            "panel-card px-4 py-2 fs-small items-center gap-4 flex-wrap mb-6 w-full"
        ):
            ui.label(f"{n} × {n}").classes("font-bold text-main")
            ui.label(ETIQUETAS_METODO.get(metodo, metodo)).classes("font-semibold text-main")
            ui.label(f"Pasos: {total}").classes("text-sec")
            if metodo == METODO_LU:
                ui.label(f"Intercambios: {resultado.get('swap_count', 0)}").classes("text-sec")
            ui.label(f"calculado en {tiempo} s").classes("text-sec")
        if getattr(self, "ai_panel", None) is not None:
            self.ai_panel.render_inline_chips()

    def _pintar_tarjeta_resultado(self, resultado: dict[str, Any]) -> None:
        """Dibuja la tarjeta con la fórmula, el valor exacto, las acciones y los decimales."""
        with ui.column().classes("panel-card p-6 w-full mb-6"):
            ui.label("Resultado: det(A)").classes("text-lg font-bold text-main mb-4")
            _pintar_formula(resultado)
            ui.label(f"det(A) = {resultado['determinante_str']}").classes("det-valor mt-2")
            _pintar_acciones(resultado)
            _pintar_decimal(resultado)