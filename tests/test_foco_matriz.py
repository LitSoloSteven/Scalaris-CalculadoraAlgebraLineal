"""Pruebas del foco y detalle de pasos para operaciones matriciales."""
from fractions import Fraction
import pytest

from src.ai.context import AIContext, StepRef
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import (
    EvaluadorExpresionesMatriciales,
)
from src.frontend.components.ai_panel import AIPanel
from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


class MockAIPanel(AIPanel):
    def __init__(self, active_ui, storage_dict=None):
        self._mock_storage = storage_dict if storage_dict is not None else {"ai_ctx_enabled": True}
        super().__init__(active_ui)

    @property
    def _storage(self):
        return self._mock_storage


def test_foco_matriz_suma():
    evaluador = EvaluadorExpresionesMatriciales()
    matriz_a = Matriz(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    matriz_b = Matriz(2, 2, [[Fraction(5), Fraction(6)], [Fraction(7), Fraction(8)]])
    resultado = evaluador.evaluar("A+B", {"A": matriz_a, "B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert len(resultado["segment_steps"]) == 1

    paso = resultado["segment_steps"][0]
    foco = ControladorOperacionesMatrices.construir_foco_paso(paso, 1, 1)

    assert foco["index"] == 1
    assert foco["total"] == 1
    assert foco["kind"] == "otro"
    assert "Suma" in foco["op"]
    assert "T1" in foco["op"]
    assert "A" in foco["op"] and "B" in foco["op"]
    assert r"\cdot" not in foco["op"]
    assert "{" not in foco["op"] and "}" not in foco["op"]

    assert foco["detail"] is not None
    assert foco["detail"]["forma"] == "2×2"
    assert "ejemplo" in foco["detail"]
    assert foco["detail"]["ejemplo"].startswith("Celda (1, 1)")
    assert len(foco["detail"]["ejemplo"]) <= 120
    assert foco["detail"]["ejemplo"] != paso["cell_by_cell_steps"][0]["description"]


def test_foco_matriz_multiplicacion():
    evaluador = EvaluadorExpresionesMatriciales()
    matriz_a = Matriz(2, 3, [[Fraction(1), Fraction(2), Fraction(0)], [Fraction(3), Fraction(4), Fraction(1)]])
    matriz_b = Matriz(3, 2, [[Fraction(2), Fraction(1)], [Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]])
    resultado = evaluador.evaluar("AB", {"A": matriz_a, "B": matriz_b})
    assert resultado["status"] == "SUCCESS"
    assert len(resultado["segment_steps"]) == 1

    paso = resultado["segment_steps"][0]
    foco = ControladorOperacionesMatrices.construir_foco_paso(paso, 1, 1)

    assert foco["index"] == 1
    assert foco["total"] == 1
    assert foco["kind"] == "otro"
    assert "Multiplicación" in foco["op"]
    assert "T1" in foco["op"]
    assert r"\cdot" not in foco["op"]
    assert "{" not in foco["op"] and "}" not in foco["op"]

    assert foco["detail"] is not None
    assert foco["detail"]["forma"] == "2×2"
    assert "ejemplo" in foco["detail"]
    assert foco["detail"]["ejemplo"].startswith("Fila 1 de A")
    assert len(foco["detail"]["ejemplo"]) <= 120
    assert foco["detail"]["ejemplo"] != paso["cell_by_cell_steps"][0]["description"]


def test_foco_matriz_transpuesta():
    evaluador = EvaluadorExpresionesMatriciales()
    matriz_a = Matriz(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    resultado = evaluador.evaluar("A^T", {"A": matriz_a})
    assert resultado["status"] == "SUCCESS"
    assert len(resultado["segment_steps"]) == 1

    paso = resultado["segment_steps"][0]
    foco = ControladorOperacionesMatrices.construir_foco_paso(paso, 1, 1)

    assert foco["index"] == 1
    assert foco["total"] == 1
    assert foco["kind"] == "otro"
    assert foco["detail"] is not None
    assert foco["detail"]["forma"] == "2×2"
    assert "ejemplo" not in foco["detail"]


def test_panel_ia_recolectar_contexto_detalle_paso():
    class InterfazSimulada:
        def get_ai_context(self):
            return AIContext(
                tool="matrix_ops",
                view="Matrices",
                label="Matriz A y B",
                input={"expresion": "AB"},
            )

    panel = MockAIPanel(InterfazSimulada(), {"ai_ctx_enabled": True})

    panel.explain_focus = {
        "index": 1,
        "total": 1,
        "kind": "otro",
        "op": "Multiplicación: T1 = A * B",
        "detail": {"forma": "2×2", "ejemplo": "Celda (1, 1): 1*2 = 2"},
    }

    ctx_text = panel._collect_context()
    assert "2×2" in ctx_text or "Multiplicación" in ctx_text
