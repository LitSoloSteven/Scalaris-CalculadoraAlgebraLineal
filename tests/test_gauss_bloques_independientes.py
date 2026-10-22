"""Reducción de bloques independientes y compatibilidad de sistemas con un vector."""
from tests.comun_entradas import copiar_entrada_prueba
from fractions import Fraction
import pytest
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.sistemas_lineales.gauss_jordan import ResolutorGaussJordan


def _aumentar_con_identidad(valores, dimension):
    filas = []
    for i in range(dimension):
        fila = [Fraction(valor) for valor in valores[i]]
        for j in range(dimension):
            fila.append(Fraction(1) if i == j else Fraction(0))
        filas.append(fila)
    return Matriz(dimension, 2 * dimension, filas)


def test_bloque_independiente_predeterminado_es_una_columna():
    """El resolutor conserva un vector independiente como valor predeterminado."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    assert ResolutorGauss(matriz).numero_terminos_independientes == 1


def test_numero_de_columnas_independientes_debe_ser_entero_positivo():
    """Los tamaños nulos, negativos y no enteros conservan el error de validación."""
    matriz = Matriz(2, 3, [[1, 2, 3], [4, 5, 6]])
    with pytest.raises(ValueError, match="numero_terminos_independientes"):
        ResolutorGauss(matriz, numero_terminos_independientes=0)
    with pytest.raises(ValueError, match="numero_terminos_independientes"):
        ResolutorGauss(matriz, numero_terminos_independientes=-1)
    with pytest.raises(ValueError, match="numero_terminos_independientes"):
        ResolutorGauss(matriz, numero_terminos_independientes=1.5)


def test_resolucion_de_sistema_rechaza_varias_columnas_independientes():
    """La resolución con sustitución conserva su contrato de una columna independiente."""
    matriz = Matriz(2, 4, [[1, 2, 1, 0], [3, 4, 0, 1]])
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=2)
    with pytest.raises(ValueError, match="numero_terminos_independientes"):
        resolutor.resolver()


def test_reduccion_dos_por_dos_produce_identidad_e_inversa():
    """La reducción del bloque aumentado produce los dos bloques exactos."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=2)
    resultado = resolutor.resolver_reduccion()
    reducida = resultado["matriz_reducida"]
    assert resultado["rango"] == 2
    assert resultado["columnas_pivote"] == [0, 1]
    for i in range(2):
        for j in range(2):
            esperado = Fraction(1) if i == j else Fraction(0)
            assert reducida.obtener(i, j) == esperado
    assert reducida.obtener(0, 2) == Fraction(4, 7)
    assert reducida.obtener(0, 3) == Fraction(-3, 7)
    assert reducida.obtener(1, 2) == Fraction(-3, 14)
    assert reducida.obtener(1, 3) == Fraction(2, 7)


def test_reduccion_tres_por_tres_conserva_inversa_exacta():
    """La reducción con pivote inicial nulo mantiene la inversa racional."""
    matriz = _aumentar_con_identidad([[0, 1, 2], [1, 0, 3], [4, -3, 8]], 3)
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=3)
    resultado = resolutor.resolver_reduccion()
    reducida = resultado["matriz_reducida"]
    assert resultado["rango"] == 3
    inversa_esperada = copiar_entrada_prueba('inversa_tres_por_tres')
    for i in range(3):
        for j in range(3):
            assert reducida.obtener(i, 3 + j) == inversa_esperada[i][j]


def test_reduccion_singular_tiene_rango_deficiente():
    """La matriz dependiente conserva rango menor que su dimensión."""
    matriz = _aumentar_con_identidad([[1, 2], [2, 4]], 2)
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=2)
    resultado = resolutor.resolver_reduccion()
    assert resultado["rango"] < 2
    reducida = resultado["matriz_reducida"]
    assert reducida.obtener(0, 0) == Fraction(1)
    assert reducida.obtener(1, 0) == Fraction(0)
    assert reducida.obtener(1, 1) == Fraction(0)


def test_reduccion_devuelve_pasos_y_metadatos():
    """El contrato conserva matriz reducida, rango, pivotes y pasos."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=2)
    resultado = resolutor.resolver_reduccion()
    assert "pasos" in resultado
    assert len(resultado["pasos"]) > 0
    assert "inicial" in resultado["pasos"][0]["descripcion"].lower()
    assert "matriz_reducida" in resultado
    assert "rango" in resultado
    assert "columnas_pivote" in resultado


def test_sistema_de_una_columna_independiente_conserva_solucion():
    """La resolución habitual conserva la solución exacta del sistema."""
    matriz = Matriz(3, 4, [[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]])
    resultado = ResolutorGauss(matriz).resolver()
    assert resultado["estado"] == "SOLUCION_UNICA"
    assert resultado["solucion_exacta"] == [Fraction(2), Fraction(3), Fraction(-1)]


def test_reduccion_conserva_denominador_grande():
    """El bloque inverso conserva fracciones con denominador mayor que mil."""
    matriz = _aumentar_con_identidad([[1001, 0], [0, 1001]], 2)
    resolutor = ResolutorGaussJordan(matriz, numero_terminos_independientes=2)
    resultado = resolutor.resolver_reduccion()
    reducida = resultado["matriz_reducida"]
    assert reducida.obtener(0, 2) == Fraction(1, 1001)
    assert reducida.obtener(1, 3) == Fraction(1, 1001)


def test_reduccion_no_modifica_matriz_original():
    """La reducción conserva intacta la matriz recibida."""
    matriz = _aumentar_con_identidad([[4, 6], [3, 8]], 2)
    original = matriz.clonar()
    ResolutorGaussJordan(matriz, numero_terminos_independientes=2).resolver_reduccion()
    assert matriz == original
