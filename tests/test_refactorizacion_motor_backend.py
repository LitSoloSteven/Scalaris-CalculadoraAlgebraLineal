"""Comportamiento del motor comun, sus opciones y los datos consumidos por las trazas."""
from fractions import Fraction

import pytest

from src.backend.modelos.construcciones import identidad
from src.backend.modelos.calculo_matricial import multiplicar_matrices
from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.sistemas_lineales.configuracion_reduccion import ConfiguracionReduccion
from src.backend.resolutores.sistemas_lineales.reduccion import ReductorFilas
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.backend.resolutores.operaciones_matrices.calculo_determinante import triangular_y_determinante
from src.backend.resolutores.sistemas_lineales.calculo_solucion import calcular_solucion_parametrica
from src.backend.resolutores.sistemas_lineales.presentacion_sustitucion import presentar_sustitucion


@pytest.mark.parametrize("datos", [
    [[4, 2], [6, 5]], [[0, 1, 2], [0, 2, 5]],
    [[1, 2], [2, 4]], [[2, 1], [4, 3], [6, 5]],
])
def test_factores_sin_intercambios_reconstruyen_matriz(datos):
    """Los multiplicadores reconstruyen matrices regulares, singulares y rectangulares con columnas nulas."""
    matriz = Matriz(len(datos), len(datos[0]), datos)
    configuracion = ConfiguracionReduccion(estrategia_pivote="sin_intercambios",
                                         normalizar_pivotes=False, capturar_multiplicadores=True)
    resultado = ReductorFilas(matriz, matriz.columnas, configuracion).reducir()
    inferior = identidad(matriz.filas)
    for factor in resultado["multiplicadores"]:
        inferior.establecer(factor["fila"], factor["columna"], factor["valor"])
    producto = multiplicar_matrices(inferior, resultado["matriz_reducida"])
    assert producto.datos == matriz.datos
    assert resultado["pivote_bloqueado"] is None
    assert resultado["intercambios"] == 0


def test_pivote_bloqueado_conserva_coordenada_sin_permutar():
    """Un cero con entrada inferior no nula detiene la reduccion y exige intercambio."""
    matriz = Matriz(2, 2, [[0, 1], [2, 3]])
    opciones = ConfiguracionReduccion(estrategia_pivote="sin_intercambios", normalizar_pivotes=False)
    resultado = ReductorFilas(matriz, 2, opciones).reducir()
    assert resultado["pivote_bloqueado"] == (0, 0)
    assert resultado["intercambios"] == 0
    assert resultado["matriz_reducida"].datos == matriz.datos


def test_resolver_no_presenta_como_solucion_una_reduccion_bloqueada():
    """El resolutor de sistemas informa el bloqueo en lugar de clasificar una reduccion incompleta."""
    opciones = ConfiguracionReduccion(estrategia_pivote="sin_intercambios")
    with pytest.raises(ValueError, match="intercambiar filas"):
        ResolutorGauss(Matriz(2, 3, [[0, 1, 2], [1, 0, 3]]), configuracion=opciones).resolver()


def test_determinante_bloqueado_no_informa_singularidad_falsa():
    """La falta de intercambio requerido informa error y nunca un determinante nulo inventado."""
    matriz = Matriz(2, 2, [[0, 1], [1, 0]])
    with pytest.raises(ValueError, match="intercambiar filas"):
        triangular_y_determinante(matriz, estrategia="sin_intercambios")
    assert triangular_y_determinante(matriz, estrategia="parcial")[0] == -1
    assert triangular_y_determinante(matriz)[0] == -1


def test_presentacion_no_agrega_etiquetas_a_parametros_de_dominio():
    """Presentar la solucion incorpora etiquetas en su respuesta y conserva la entrada numerica."""
    matriz = Matriz(1, 3, [[1, 1, 0]])
    parametros = calcular_solucion_parametrica(matriz, [0], 2)
    original = dict(parametros)
    presentacion = presentar_sustitucion(parametros, [0], ["x", "y"])
    assert parametros == original
    assert presentacion[4] is not parametros
    assert presentacion[4]["nombres_parametros"] == ["t"]


def test_pivoteo_parcial_elige_maximo_y_conserva_entrada():
    """El modo parcial usa el maximo absoluto y los pasos poseen copias independientes."""
    matriz = Matriz(2, 3, [[2, 1, 5], [-9, 2, -7]])
    resolutor = ResolutorGauss(matriz)
    resultado = resolutor.resolver_reduccion()
    assert resolutor.intercambios == 1
    assert resultado["pasos"][1]["matriz"].datos[0] == [-9, 2, -7]
    resultado["matriz_reducida"].establecer(0, 0, Fraction(999))
    assert resultado["pasos"][0]["matriz"].datos == [[2, 1, 5], [-9, 2, -7]]
    assert matriz.datos == [[2, 1, 5], [-9, 2, -7]]


@pytest.mark.parametrize("opciones", [
    {"estrategia_pivote": "desconocida"}, {"tolerancia_cero": -1},
    {"tolerancia_cero": float("nan")}, {"tolerancia_cero": float("inf")},
    {"tolerancia_cero": True}, {"capturar_multiplicadores": True},
    {"normalizar_pivotes": 1},
    {"capturar_multiplicadores": True, "estrategia_pivote": "sin_intercambios", "reduccion_completa": True},
])
def test_opciones_invalidas_se_rechazan_antes_de_reducir(opciones):
    """La configuracion rechaza tipos y combinaciones incoherentes con ValueError."""
    with pytest.raises(ValueError):
        ConfiguracionReduccion(**opciones)
