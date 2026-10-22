"""Comprobaciones exactas, simbolicas y negativas con datos distintos del texto renderizado."""
from fractions import Fraction
import json

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.modelos.construcciones import identidad
from src.backend.resolutores.operaciones_matrices.comprobacion_productos import comprobar_producto
from src.backend.resolutores.operaciones_matrices.inversa import ResolutorInversa
from src.backend.resolutores.operaciones_matrices.captura_inversa import extraer_comprobaciones_inversa
from src.backend.resolutores.operaciones_matrices.transformaciones import ResolutorTransformacionesLineales
from src.backend.resolutores.operaciones_matrices.leontief import ResolutorModeloLeontief
from src.backend.resolutores.operaciones_vectores.combinacion_lineal import ResolutorCombinacionLineal
from src.backend.resolutores.sistemas_lineales.comprobacion_sistemas import comprobar_familia
from src.backend.resolutores.sistemas_lineales.gauss import ResolutorGauss
from src.frontend.controladores.sistemas_lineales import ControladorGauss, ControladorGaussJordan


def test_producto_fallido_no_afirma_igualdad_y_mantiene_desarrollo():
    """Una candidata incorrecta conserva la sustitucion y compara mediante desigualdad."""
    resultado = comprobar_producto(Matriz(1, 2, [["1/2", -2]]), Matriz(2, 1, [[2], [3]]), Matriz(1, 1, [[0]]), "Ax=b")
    assert not resultado["coincide"]
    assert resultado["producto"].datos == [[-5]]
    assert r"\ne" in resultado["traza"][-1]["detalle_latex"]
    assert "(-2)(3)" in resultado["traza"][1]["detalle_latex"]


@pytest.mark.parametrize("datos", [[["3/7"]], [[0, 1], [2, 3]], [["1/2", "1/3"], ["2/3", "3/4"]]])
def test_inversa_desarrolla_ambos_productos_y_propiedad_transpuesta(datos):
    """Cada identidad conserva todas sus celdas y explica que no se invirtio A transpuesta."""
    matriz = Matriz(len(datos), len(datos), datos)
    resultado = ResolutorInversa().resolver(matriz)
    for clave in ("paso_verificacion", "paso_verificacion_inverso", "paso_propiedad_transpuesta"):
        paso = resultado[clave]
        assert paso["coincide"]
        assert len(paso["traza"]) == len(datos) ** 2 + 2
        assert r"\begin{bmatrix}" in paso["traza"][-1]["detalle_latex"]
    assert "no se ha invertido" in resultado["paso_propiedad_transpuesta"]["traza"][-1]["explicacion"]


def test_inversa_grande_conserva_desarrollo_aunque_omita_resumen_latex():
    """El limite visual de matrices grandes no elimina la comprobacion por celdas."""
    resultado = ResolutorInversa().resolver(identidad(9))
    comprobaciones = extraer_comprobaciones_inversa(resultado, 9)
    assert len(comprobaciones) == 3
    assert all(len(paso["traza"]) == 83 for paso in comprobaciones)


def _familia():
    aumentada = Matriz(2, 4, [["1/2", 1, -1, "1/3"], [1, 2, -2, "2/3"]])
    return aumentada, ResolutorGauss(aumentada).resolver()["parametros_solucion"]


def test_familia_afin_se_comprueba_para_todos_los_parametros():
    """La comprobacion agrupa todos los parametros sin elegir valores particulares."""
    aumentada, familia = _familia()
    resultado = comprobar_familia([fila[:3] for fila in aumentada.datos], [fila[3] for fila in aumentada.datos], familia)
    assert resultado["coincide"]
    assert [fila["constante"] for fila in resultado["filas"]] == [Fraction(1, 3), Fraction(2, 3)]
    assert all(fila["coeficientes_parametros"] == [0, 0] for fila in resultado["filas"])
    assert all("todos los parametros" in detalle for detalle in resultado["pasos_latex"])


def test_direccion_erronea_falla_aunque_particular_satisfaga_el_sistema():
    """Comprobar solo el punto particular no certifica la familia completa."""
    aumentada, familia = _familia()
    familia["direcciones"][0][0] += 1
    resultado = comprobar_familia([fila[:3] for fila in aumentada.datos], [fila[3] for fila in aumentada.datos], familia)
    assert not resultado["coincide"]
    assert all(r"\not\equiv" in detalle for detalle in resultado["pasos_latex"])


@pytest.mark.parametrize("controlador", [ControladorGauss, ControladorGaussJordan])
def test_controladores_comprueban_parametrica_con_etiquetas_originales(controlador):
    """La presentacion no convierte expresiones de la solucion en numeros."""
    carga = {"matriz_a": [[1, 2], [2, 4]], "vector_b": [3, 6], "variables": ["a", "b"]}
    respuesta = json.loads(controlador.procesar_sistema(json.dumps(carga)))
    assert respuesta["estado"] == "SOLUCIONES_INFINITAS"
    assert len(respuesta["pasos_verificacion_latex"]) == 2
    assert all("todos los parametros" in paso for paso in respuesta["pasos_verificacion_latex"])
    assert "(1)a" in respuesta["pasos_verificacion_latex"][0]


@pytest.mark.parametrize("datos", [[[1, 2, 3], [2, 4, 6]], [[0, 0], [0, 0]], [[1, 0], [0, 1]], [["1/2", "1/3"], [1, "2/3"]]])
def test_transformacion_desarrolla_nucleo_imagen_y_dimension(datos):
    """Se desarrolla la familia nula, la preimagen canonica y la generacion A=BR."""
    matriz = Matriz(len(datos), len(datos[0]), datos)
    resultado = ResolutorTransformacionesLineales().resolver(matriz)
    traza = resultado["traza_comprobacion"]
    assert any("Nucleo: ecuacion" in paso["descripcion"] for paso in traza)
    assert traza[-1]["descripcion"] == "Dimension y propiedades"
    if resultado["rango"]:
        assert any("A=BR" in paso["descripcion"] for paso in traza)
        assert any("T(e_" in paso["descripcion"] for paso in traza)
        assert not any("no coincide" in paso["descripcion"] for paso in traza)
    else:
        assert any(paso["descripcion"] == "Imagen nula" for paso in traza)


@pytest.mark.parametrize("datos,demanda", [([["1/2", 0], [0, "1/3"]], [1, 2]), ([[1]], [1]), ([[0]], [Fraction(-1, 3)])])
def test_leontief_muestra_balance_y_menores_con_signo(datos, demanda):
    """El caso singular desarrolla el menor cero sin inventar una produccion."""
    resultado = ResolutorModeloLeontief().resolver(Matriz(len(datos), len(datos), datos), demanda)
    traza = resultado["traza_comprobacion"]
    assert any("Positividad del menor" in paso["descripcion"] for paso in traza)
    balance = [paso for paso in traza if "Balance del sector" in paso["descripcion"]]
    if resultado["estado"] == "EXITO":
        assert len(balance) == len(datos)
    else:
        assert resultado["estado"] in {"SIN_SOLUCION", "SOLUCIONES_INFINITAS"}
        assert balance == [] and resultado["determinante_leontief"] == "0"
        assert "vector_produccion" not in resultado
    assert all("Cx" in paso["detalle_latex"] for paso in balance)


@pytest.mark.parametrize("vectores,objetivo", [([[[1], [2]], [[2], [4]]], [[3], [6]]), ([[[1], [0]], [[0], [1]]], [["1/2"], ["2/3"]])])
def test_combinacion_desarrolla_componentes_para_unica_y_familia(vectores, objetivo):
    """La representacion unica y las infinitas tienen sustitucion por componentes."""
    columnas = [Matriz(2, 1, vector) for vector in vectores]
    resultado = ResolutorCombinacionLineal().resolver(Matriz(2, 1, objetivo), columnas)
    if resultado["estado"] == "UNICA":
        assert len(resultado["paso_verificacion"]["traza"]) == 4
    else:
        assert len(resultado["traza_comprobacion"]) == 2
        assert all("parametros" in paso["detalle_latex"] for paso in resultado["traza_comprobacion"])


def test_comprobacion_rechaza_dimensiones_truncadas():
    """Ningun zip puede certificar una familia omitiendo ecuaciones o variables."""
    _, familia = _familia()
    with pytest.raises(ValueError, match="dimensiones"):
        comprobar_familia([[1]], [0], familia)
    with pytest.raises(ValueError, match="independiente"):
        comprobar_familia([[1, 2, 3]], [], familia)


def test_coeficientes_negativos_no_certifican_viabilidad_por_hawkins_simon():
    """Los datos siguen siendo resolubles sin afirmar un criterio fuera de sus hipotesis."""
    resultado = ResolutorModeloLeontief().resolver(Matriz(2, 2, [[0, -2], [-2, 0]]), [1, 1])
    assert resultado["estado"] == "EXITO"
    assert resultado["hawkins_simon"]["criterio_aplicable"] is False
    assert resultado["hawkins_simon"]["es_economicamente_viable"] is None
    assert "no certifica" in resultado["hawkins_simon"]["conclusion"]


@pytest.mark.parametrize("datos", [[[0]], [[1, 2], [2, 4]], [[0, 1, 2], [0, 2, 4], [1, 0, 0]]])
def test_inversa_singular_desarrolla_el_determinante_ejecutado(datos):
    """La falta de inversa se explica con la eliminacion real y su producto diagonal."""
    resultado = ResolutorInversa().resolver(Matriz(len(datos), len(datos), datos))
    assert resultado["estado"] == "SINGULAR"
    assert resultado["inversa"] is None
    assert resultado["traza_determinante"]
    assert "=0" in resultado["traza_determinante"][-1]["detalle_latex"]
    assert "no un segundo metodo" in resultado["traza_determinante"][-1]["explicacion"]
    assert not any("mayor valor absoluto" in paso["explicacion"] for paso in resultado["traza_determinante"])
