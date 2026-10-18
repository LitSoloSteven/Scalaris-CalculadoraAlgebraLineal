"""Pruebas del foco y detalle de pasos para operaciones matriciales."""
from fractions import Fraction
import pytest

from src.ai.contexto import ContextoIA
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.evaluador import (
    EvaluadorExpresionesMatriciales,
)
from tests.comun_clientes import PanelIASimulado
from tests.comun_foco_matriz import evaluar_foco_matriz, comprobar_ejemplo_foco
from src.frontend.controladores.operaciones_matrices.controlador_operaciones_matrices import (
    ControladorOperacionesMatrices,
)


def test_foco_matriz_suma():
    """El foco de suma conserva operación y ejemplo breve de una celda."""
    matriz_a = Matriz(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    matriz_b = Matriz(2, 2, [[Fraction(5), Fraction(6)], [Fraction(7), Fraction(8)]])
    paso, foco = evaluar_foco_matriz("A+B", {"A": matriz_a, "B": matriz_b})
    assert "Suma" in foco["operacion"]
    assert "T1" in foco["operacion"]
    assert "A" in foco["operacion"] and "B" in foco["operacion"]
    assert r"\cdot" not in foco["operacion"]
    assert "{" not in foco["operacion"] and "}" not in foco["operacion"]

    comprobar_ejemplo_foco(foco, paso, "Celda (1, 1)")


def test_foco_matriz_multiplicacion():
    """El foco de producto conserva forma y ejemplo de fila por columna."""
    matriz_a = Matriz(2, 3, [[Fraction(1), Fraction(2), Fraction(0)], [Fraction(3), Fraction(4), Fraction(1)]])
    matriz_b = Matriz(3, 2, [[Fraction(2), Fraction(1)], [Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]])
    paso, foco = evaluar_foco_matriz("AB", {"A": matriz_a, "B": matriz_b})
    assert "Multiplicación" in foco["operacion"]
    assert "T1" in foco["operacion"]
    assert r"\cdot" not in foco["operacion"]
    assert "{" not in foco["operacion"] and "}" not in foco["operacion"]

    comprobar_ejemplo_foco(foco, paso, "Fila 1 de A")


def test_foco_matriz_transpuesta():
    """El foco de transposición conserva forma y ausencia de ejemplo de celda."""
    matriz_a = Matriz(2, 2, [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]])
    paso, foco = evaluar_foco_matriz("A^T", {"A": matriz_a})
    assert foco["detalle"] is not None
    assert foco["detalle"]["forma"] == "2×2"
    assert "ejemplo" not in foco["detalle"]


def test_panel_ia_recolectar_contexto_detalle_paso():
    """El panel adjunta el detalle del paso seleccionado al ejercicio actual."""
    class InterfazSimulada:
        """Entrega el ejercicio matricial mediante el contrato de contexto vigente."""
        def obtener_contexto_ia(self):
            """Devuelve las entradas del ejercicio para su explicación."""
            return ContextoIA(
                herramienta="operaciones_matrices",
                vista="Matrices",
                etiqueta="Matriz A y B",
                entrada={"expresion": "AB"},
            )

    panel = PanelIASimulado(InterfazSimulada(), {"ia_contexto_habilitado": True})

    panel.foco_explicacion = {
        "indice": 1,
        "total": 1,
        "tipo": "otro",
        "operacion": "Multiplicación: T1 = A * B",
        "detalle": {"forma": "2×2", "ejemplo": "Celda (1, 1): 1*2 = 2"},
    }

    texto_contexto = panel._recopilar_contexto()
    assert "2×2" in texto_contexto or "Multiplicación" in texto_contexto
