"""Contexto, señales y foco de Glosa para la vista de Determinantes."""
from __future__ import annotations

from typing import Any

from src.ai.context import (
    AIContext,
    compact_number,
    describe_matrix,
    is_stale,
    sanitize_user_string,
    window_note_from,
)
from src.frontend.suggestions import Signals, first_invalid_cell
from src.frontend.views.determinant_ops._config import AI_CONTEXT_MAX_N
from src.frontend.views.determinant_ops.metodo_mixin import METODO_COFACTORES, METODO_LU

HERRAMIENTA_GLOSA = "determinantes"
VISTA_GLOSA = "Determinantes"
LIMITE_TEXTO_CELDA = 32
ESTADOS_GLOSA = {"SUCCESS": "success", "SINGULAR": "singular"}


class DeterminantOpsAiMixin:
    """Expone a Glosa los datos de entrada, el resultado vigente y el foco de celda.

    Requiere en la vista: square_panel, method_tabs, last_result, _result_fp y ai_panel.
    """

    def _refrescar_glosa(self) -> None:
        """Pide a Glosa que actualice su contexto, si el panel existe."""
        panel = getattr(self, "ai_panel", None)
        if panel is not None and hasattr(panel, "schedule_context_refresh"):
            panel.schedule_context_refresh()

    def _entrada_actual(self) -> dict[str, Any]:
        """Devuelve la entrada que identifica un resultado: matriz y método."""
        return {"data": self.square_panel.get_matrix_data(), "metodo": self.method_tabs.value}

    def _resultado_vigente(self) -> dict[str, Any] | None:
        """Devuelve el último resultado solo si la entrada no cambió desde el cálculo."""
        if not self.last_result:
            return None
        if is_stale(self._entrada_actual(), self._result_fp):
            return None
        return self.last_result

    def get_ai_context(self) -> AIContext:
        """Construye el contexto de Glosa con la matriz, el método y el resultado vigente."""
        n = self.square_panel.n
        if self.square_panel.is_empty():
            return AIContext(
                tool=HERRAMIENTA_GLOSA, view=VISTA_GLOSA, label="Matriz A", input={}, empty=True
            )
        entrada = self._entrada_actual()
        saneada = [
            [sanitize_user_string(celda, LIMITE_TEXTO_CELDA) for celda in fila]
            for fila in entrada["data"]
        ]
        descripcion = describe_matrix(saneada)
        contexto = AIContext(
            tool=HERRAMIENTA_GLOSA,
            view=VISTA_GLOSA,
            label=f"A ({n}×{n})",
            input={"A": descripcion, "metodo": entrada["metodo"]},
        )
        contexto.window_note = window_note_from(descripcion)
        contexto.stale = is_stale(entrada, self._result_fp)
        vigente = None if contexto.stale else self.last_result
        if vigente:
            contexto.result = self._resumen_para_glosa(vigente, n)
        return contexto

    def _resumen_para_glosa(self, resultado: dict[str, Any], n: int) -> dict[str, Any]:
        """Resume el resultado; con matrices grandes solo estado, valor y método."""
        if resultado.get("status") not in ESTADOS_GLOSA:
            return {"status": "ERROR"}
        determinante = resultado.get("determinante_str")
        resumen = {
            "status": resultado["status"],
            "determinante": compact_number(determinante) if determinante is not None else None,
            "metodo": resultado.get("metodo"),
        }
        if n > AI_CONTEXT_MAX_N:
            return resumen
        resumen["pasos_totales"] = (resultado.get("stats") or {}).get("total", 0)
        resumen["es_singular"] = bool(resultado.get("es_singular"))
        if resultado.get("metodo") == METODO_LU:
            resumen["intercambios"] = resultado.get("swap_count", 0)
        return resumen

    def get_ai_signals(self) -> Signals | None:
        """Devuelve las señales que Glosa usa para sugerir preguntas, o None si fallan."""
        try:
            n = self.square_panel.n
            datos = self.square_panel.get_matrix_data()
            celdas = [
                (f"A[{i + 1},{j + 1}]", datos[i][j], (i, j))
                for i in range(n)
                for j in range(n)
            ]
            estado, banderas = self._estado_y_banderas()
            return Signals(
                tool=HERRAMIENTA_GLOSA,
                state=estado,
                flags=frozenset(banderas),
                invalid=first_invalid_cell(celdas),
            )
        except Exception:
            return None

    def _estado_y_banderas(self) -> tuple[str, set[str]]:
        """Deriva el estado y las banderas del resultado vigente."""
        resultado = self._resultado_vigente()
        if not resultado:
            return "none", set()
        estado = ESTADOS_GLOSA.get(resultado.get("status"), "none")
        banderas: set[str] = set()
        metodo = resultado.get("metodo")
        if metodo == METODO_LU and resultado.get("swap_count", 0) > 0:
            banderas.add("swap")
        if metodo == METODO_COFACTORES and estado != "none":
            banderas.add("signos")
        return estado, banderas

    def focus_cell(self, focus: tuple[int, int] | None) -> None:
        """Resalta la celda indicada por Glosa en el panel de captura."""
        if focus and hasattr(self, "square_panel"):
            self.square_panel.flash_cell(*focus)
