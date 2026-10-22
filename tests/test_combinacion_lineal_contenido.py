"""Contenido exacto del planteamiento, comprobación y numeración de combinaciones."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal
from tests.comun_combinacion import preparar_combinacion_canonica


def test_combinacion_canonica_latex_y_numeracion():
    """Conserva los tres vectores, la ecuación comprobada y el orden de todos los pasos."""
    resolutor, primero, segundo, objetivo, resultado = preparar_combinacion_canonica()
    planteamiento = resultado['pasos_planteamiento']
    assert r'\begin{bmatrix} 1 \\ -2 \\ -5 \end{bmatrix}' in planteamiento[0]['detalle_latex']
    assert r'\begin{bmatrix} 2 \\ 5 \\ 6 \end{bmatrix}' in planteamiento[0]['detalle_latex']
    assert r'\begin{bmatrix} 7 \\ 4 \\ -3 \end{bmatrix}' in planteamiento[0]['detalle_latex']
    assert r'\begin{cases}' in planteamiento[3]['detalle_latex']
    assert r'array}{cc|c}' in planteamiento[4]['detalle_latex']
    comprobacion = resultado['paso_verificacion']
    assert r'\mathbf{y} = 3\mathbf{a}_1 + 2\mathbf{a}_2' in comprobacion['detalle_latex']
    assert r'\begin{bmatrix} 7 \\ 4 \\ -3 \end{bmatrix} = \mathbf{b}' in comprobacion['detalle_latex']
    assert len(resultado['pasos']) == len(planteamiento) + len(resultado['pasos_gauss'])
    for indice, paso in enumerate(resultado['pasos'], start=1):
        assert paso['numero_paso'] == indice
        assert 'Paso 0' not in paso['descripcion']
        assert not paso['descripcion'].startswith('0.')
    for paso in resultado['pasos_gauss']:
        assert 'Matriz inicial aumentada' not in paso['descripcion']
    incompatible = resolutor.resolver(Matriz(3, 1, [[1], [1], [100]]), [primero, segundo],
                                     nombres_variables=['x_1', 'x_2'], nombres_vectores=['a_1', 'a_2'])
    assert incompatible['estado'] == 'SIN_SOLUCION'
    assert len(incompatible['pasos_planteamiento']) == 5
    assert incompatible['paso_verificacion'] is None
    error = resolutor.resolver(objetivo, [])
    assert error['estado'] == 'ERROR'
    assert error['pasos_planteamiento'] == []


def test_combinacion_fraccionaria_conserva_sustitucion_exacta():
    """Mantiene coeficientes racionales y sus paréntesis sin aproximaciones decimales."""
    primero = Matriz(2, 1, [[2], [0]])
    segundo = Matriz(2, 1, [[0], [3]])
    objetivo = Matriz(2, 1, [[1], [1]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [primero, segundo],
                                                   nombres_variables=['c_1', 'c_2'], nombres_vectores=['v_1', 'v_2'])
    assert resultado['coeficientes'] == [Fraction(1, 2), Fraction(1, 3)]
    planteamiento = resultado['pasos_planteamiento']
    assert len(planteamiento) == 5
    for paso in planteamiento:
        assert '0.333' not in paso['detalle_latex']
        assert '0.500' not in paso['detalle_latex']
    comprobacion = resultado['paso_verificacion']
    assert comprobacion is not None
    assert '0.333' not in comprobacion['detalle_latex']
    assert '0.333' not in comprobacion['descripcion']
    assert r'\frac{1}{2}\mathbf{v}_1 + \frac{1}{3}\mathbf{v}_2' in comprobacion['detalle_latex']
    assert r'\left(\frac{1}{2}\right)' in comprobacion['sustitucion_latex']
    assert r'\left(\frac{1}{3}\right)' in comprobacion['sustitucion_latex']
    assert r'\checkmark' in comprobacion['detalle_latex']


def test_combinacion_un_vector_descripcion_y_comprobacion():
    """Mantiene el paso componente a componente y su señal de comprobación."""
    vector = Matriz(3, 1, [[2], [4], [6]])
    objetivo = Matriz(3, 1, [[6], [12], [18]])
    resultado = ResolutorCombinacionLineal().resolver(objetivo, [vector],
                                                   nombres_variables=['c_1'], nombres_vectores=['v_1'])
    assert len(resultado['pasos_planteamiento']) == 5
    assert '3. Igualdad vectorial componente a componente (un solo vector):' == resultado['pasos_planteamiento'][2]['descripcion']
    assert resultado['paso_verificacion'] is not None
    assert r'\checkmark' in resultado['paso_verificacion']['detalle_latex']
