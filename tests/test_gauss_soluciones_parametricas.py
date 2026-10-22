"""Soluciones particulares, direcciones del núcleo y parámetros de Gauss."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan


def _resolver(datos):
    filas = len(datos)
    columnas = len(datos[0])
    return ResolutorGauss(Matriz(filas, columnas, datos)).resolver()


def test_solucion_unica_sin_parametros():
    """La solución particular coincide con la solución exacta única."""
    resultado = _resolver([[1, 0, 2], [0, 1, 3]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["numero_variables"] == 2
    assert parametrica["columnas_libres"] == []
    assert parametrica["nombres_parametros"] == []
    assert parametrica["particular"] == [Fraction(2), Fraction(3)]
    assert parametrica["direcciones"] == []
    assert parametrica["particular"] == resultado["solucion_exacta"]


def test_una_variable_libre():
    """Una columna libre genera un parámetro y una dirección."""
    resultado = _resolver([[1, 1, 2]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["columnas_libres"] == [1]
    assert parametrica["nombres_parametros"] == ["t"]
    assert parametrica["particular"] == [Fraction(2), Fraction(0)]
    assert parametrica["direcciones"] == [[Fraction(-1), Fraction(1)]]


def test_dos_variables_libres():
    """Cada columna libre aporta su propia dirección independiente."""
    resultado = _resolver([[1, 1, 1, 1]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["columnas_libres"] == [1, 2]
    assert parametrica["nombres_parametros"] == ["t", "s"]
    assert parametrica["particular"] == [Fraction(1), Fraction(0), Fraction(0)]
    assert parametrica["direcciones"] == [
        [Fraction(-1), Fraction(1), Fraction(0)],
        [Fraction(-1), Fraction(0), Fraction(1)],
    ]


def test_coeficientes_parametricos_fraccionarios():
    """La solución particular y las direcciones conservan fracciones exactas."""
    resultado = _resolver([[2, 3, 1]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["particular"] == [Fraction(1, 2), Fraction(0)]
    assert parametrica["direcciones"] == [[Fraction(-3, 2), Fraction(1)]]


def test_sistema_incompatible_sin_parametrica():
    """La contradicción produce una solución paramétrica nula."""
    resultado = _resolver([[1, 1, 1], [1, 1, 2]])
    assert resultado["estado"] == "SIN_SOLUCION"
    assert resultado["parametros_solucion"] is None


def test_denominador_grande_sin_truncamiento():
    """El coeficiente particular conserva un denominador superior a mil."""
    resultado = _resolver([[1001, 1]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["particular"] == [Fraction(1, 1001)]
    assert parametrica["direcciones"] == []


def test_fila_nula_conserva_columna_libre():
    """Una fila nula deja libre la segunda variable."""
    resultado = _resolver([[1, 0, 2], [0, 0, 0]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["columnas_libres"] == [1]
    assert parametrica["particular"] == [Fraction(2), Fraction(0)]
    assert parametrica["direcciones"] == [[Fraction(0), Fraction(1)]]


def test_columna_libre_anterior_al_pivote():
    """La primera variable puede ser libre aunque haya pivote posterior."""
    resultado = _resolver([[0, 1, 5], [0, 0, 0]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["columnas_libres"] == [0]
    assert parametrica["particular"] == [Fraction(0), Fraction(5)]
    assert parametrica["direcciones"] == [[Fraction(1), Fraction(0)]]


def test_nombres_de_parametros_numerosos():
    """Después de los símbolos iniciales usa un subíndice numérico."""
    resultado = _resolver([[1, 1, 1, 1, 1, 1, 1, 1]])
    parametrica = resultado["parametros_solucion"]
    assert parametrica["numero_variables"] == 7
    assert parametrica["columnas_libres"] == [1, 2, 3, 4, 5, 6]
    assert parametrica["nombres_parametros"] == ["t", "s", "r", "u", "v", "t_6"]


def test_particular_satisface_sistema_y_direcciones_pertenecen_al_nucleo():
    """El producto matricial verifica la solución afín con aritmética exacta."""
    datos = [[1, 1, 1, 1]]
    resultado = _resolver(datos)
    parametrica = resultado["parametros_solucion"]
    coeficientes = Matriz(1, 3, [[1, 1, 1]])
    termino = Fraction(1)
    producto = sum(coeficientes.obtener(0, j) * parametrica["particular"][j] for j in range(3))
    assert producto == termino
    for direccion in parametrica["direcciones"]:
        assert sum(coeficientes.obtener(0, j) * direccion[j] for j in range(3)) == 0


def test_gauss_y_gauss_jordan_coinciden():
    """Ambos procedimientos producen la misma solución paramétrica."""
    for datos in (
        [[1, 0, 2], [0, 1, 3]], [[1, 1, 2]], [[1, 1, 1, 1]],
        [[2, 3, 1]], [[0, 1, 5], [0, 0, 0]],
    ):
        filas, columnas = len(datos), len(datos[0])
        resultado_gauss = ResolutorGauss(Matriz(filas, columnas, datos)).resolver()
        resultado_jordan = ResolutorGaussJordan(Matriz(filas, columnas, datos)).resolver()
        assert resultado_gauss["parametros_solucion"] == resultado_jordan["parametros_solucion"], datos


def _comprobar_coordenadas_libres(parametrica):
    for k, columna_libre in enumerate(parametrica["columnas_libres"]):
        assert parametrica["direcciones"][k][columna_libre] == 1
        assert parametrica["particular"][columna_libre] == 0
        for j, otra_columna in enumerate(parametrica["columnas_libres"]):
            if j != k:
                assert parametrica["direcciones"][k][otra_columna] == 0


def test_coordenadas_libres_en_distintos_tamanos():
    """Las direcciones forman la identidad en las coordenadas libres."""
    casos = [
        [[1, 2, 3, 4]],
        [[1, 0, 0, 1], [0, 1, 0, 2], [0, 0, 0, 0]],
        [[1, 1, 1, 1, 1, 1, 1, 1]],
    ]
    for datos in casos:
        filas, columnas = len(datos), len(datos[0])
        resultado = ResolutorGauss(Matriz(filas, columnas, datos)).resolver()
        parametrica = resultado["parametros_solucion"]
        if parametrica is None:
            continue
        _comprobar_coordenadas_libres(parametrica)


def test_claves_de_respuesta_preservadas():
    """La representación paramétrica conserva el resto del contrato."""
    resultado = _resolver([[1, 0, 2], [0, 1, 3]])
    for clave in (
        "solucion", "solucion_exacta", "columnas_libres", "parametros_solucion", "pasos",
        "pasos_sustitucion_regresiva", "estado", "clasificacion", "mensaje", "matriz_escalonada",
    ):
        assert clave in resultado, f"Falta la clave '{clave}'"
