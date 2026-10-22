"""Ecuaciones vectoriales completas y cálculos por componente del resultado."""
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.operaciones import ResolutorOperacionesVectores


def test_suma_resta_escalar_conservan_vector_y_componentes():
    """Verifica matrices, ecuaciones finales y tres cálculos de la suma en R³."""
    resolutor = ResolutorOperacionesVectores()
    primero = Matriz(3, 1, [[1], [-2], [5]])
    segundo = Matriz(3, 1, [[3], [4], [-1]])
    suma = resolutor.sumar(primero, segundo, nombre1='v_1', nombre2='v_2')
    assert 'matriz_resultado_latex' in suma
    assert r'\mathbf{w} =' in suma['vector_resultado_latex']
    assert r'\begin{bmatrix} 4 \\ 2 \\ 4 \end{bmatrix}' in suma['vector_resultado_latex']
    assert len(suma['detalles_latex']) == 4
    assert suma['detalles_latex'][0].startswith('w_{1}')
    assert suma['detalles_latex'][1].startswith('w_{2}')
    assert suma['detalles_latex'][2].startswith('w_{3}')
    resta = resolutor.restar(primero, segundo, nombre1='v_1', nombre2='v_2')
    assert 'vector_resultado_latex' in resta
    assert r'\mathbf{w} =' in resta['vector_resultado_latex']
    assert r'\begin{bmatrix} -2 \\ -6 \\ 6 \end{bmatrix}' in resta['vector_resultado_latex']
    escalado = resolutor.multiplicar_escalar(-3, primero, nombre='v', nombre_resultado='w')
    assert 'vector_resultado_latex' in escalado
    assert r'\mathbf{w} =' in escalado['vector_resultado_latex']
    assert r'\begin{bmatrix} -3 \\ 6 \\ -15 \end{bmatrix}' in escalado['vector_resultado_latex']
    assert len(escalado['detalles_latex']) == 4
