"""Pruebas del foco y detalle de pasos para operaciones matriciales."""
from fractions import Fraction
import pytest

from src.ai.contexto import ContextoIA
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import (
    EvaluadorExpresionesMatriciales,
)
from tests.comun_clientes import PanelIASimulado
from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def test_foco_matriz_suma():
    """El foco de suma conserva operación y ejemplo breve de una celda."""
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
    """El foco de producto conserva forma y ejemplo de fila por columna."""
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
    """El foco de transposición conserva forma y ausencia de ejemplo de celda."""
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
    """El panel adjunta el detalle del paso seleccionado al ejercicio actual."""
    class InterfazSimulada:
        """Entrega el ejercicio matricial mediante el contrato de contexto vigente."""
        def obtener_contexto_ia(self):
            """Devuelve las entradas del ejercicio para su explicación."""
            return ContextoIA(
                herramienta="matrix_ops",
                vista="Matrices",
                etiqueta="Matriz A y B",
                entrada={"expresion": "AB"},
            )

    panel = PanelIASimulado(InterfazSimulada(), {"ai_ctx_enabled": True})

    panel.explain_focus = {
        "index": 1,
        "total": 1,
        "kind": "otro",
        "op": "Multiplicación: T1 = A * B",
        "detail": {"forma": "2×2", "ejemplo": "Celda (1, 1): 1*2 = 2"},
    }

    texto_contexto = panel._collect_context()
    assert "2×2" in texto_contexto or "Multiplicación" in texto_contexto
