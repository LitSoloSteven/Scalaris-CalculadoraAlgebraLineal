"""Orden, formato e identidad de las verificaciones matriciales de inversas."""
from unittest.mock import Mock

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa


@pytest.mark.parametrize("direccion", [
    (False, "A", "A^{-1}", "A·A⁻¹"),
    (True, "A^{-1}", "A", "A⁻¹·A"),
])
@pytest.mark.parametrize("producto,cumple,latex", [
    (None, False, ""), (0, False, ""), (False, False, ""), ({}, False, ""), ([], False, ""),
    (Matriz(1, 1, [[1]]), True, "\\begin{bmatrix}\n1\n\\end{bmatrix}"),
    (Matriz(1, 1, [[2]]), False, "\\begin{bmatrix}\n2\n\\end{bmatrix}"),
])
def test_verificacion_producto_conserva_orden_y_diccionario_completo(direccion, producto, cumple, latex):
    """Ambos órdenes conservan todos los textos y el estado con producto ausente o incorrecto."""
    inverso, nombre_izquierda, nombre_derecha, descripcion_operacion = direccion
    matriz = Matriz(1, 1, [[2]])
    inversa = Matriz(1, 1, [["1/2"]])
    resolutor = ResolutorInversa()
    multiplicar = Mock(return_value={"matriz_resultado": producto})
    resolutor.resolutor_operaciones_matrices.multiplicar = multiplicar
    resultado = resolutor._verificar_producto(matriz, inversa, 1, inverso)
    esperado_izquierda, esperado_derecha = (inversa, matriz) if inverso else (matriz, inversa)
    assert multiplicar.call_count == 1
    assert multiplicar.call_args.args[0] is esperado_izquierda
    assert multiplicar.call_args.args[1] is esperado_derecha
    estado = "Correcto" if cumple else "Incorrecto"
    detalle = f"{nombre_izquierda} \\cdot {nombre_derecha} = {latex} \\quad (\\text{{{estado}}})"
    descripcion = f"Verificación {descripcion_operacion} = I."
    assert resultado == {
        "propiedad": f"{nombre_izquierda} \\cdot {nombre_derecha} = I",
        "nombre_izquierdo": nombre_izquierda, "nombre_derecho": nombre_derecha,
        "descripcion": descripcion,
        "se_cumple": cumple, "coincide": cumple,
        "matriz_producto_latex": latex,
        "detalle_latex": detalle,
    }
