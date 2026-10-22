"""Comportamiento exacto, trazas y limites de ambos metodos de determinante."""
from fractions import Fraction
from itertools import product

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices import cofactores
from src.backend.resolutores.operaciones_matrices.determinante import ResolutorDeterminante
from src.frontend.controladores.operaciones_matrices.controlador_determinante import ControladorDeterminante


@pytest.mark.parametrize("datos,esperado", [
    ([["7/13"]], Fraction(7, 13)),
    ([[0]], Fraction(0)),
    ([[1, 2], [3, 4]], Fraction(-2)),
    ([["1/2", "2/3"], ["3/4", "4/5"]], Fraction(-1, 10)),
    ([[1, 2], [2, 4]], Fraction(0)),
    ([[0, 1], [1, 0]], Fraction(-1)),
    ([[1, 2, 3], [0, 0, 4], [5, 6, 7]], Fraction(16)),
    ([[0, 1, 2], [0, 3, 4], [0, 5, 6]], Fraction(0)),
    ([["1/1000000000000", 0], [0, 1]], Fraction(1, 1000000000000)),
])
def test_metodos_coinciden_exactamente_con_captura(datos, esperado):
    """Ambas elecciones manuales conservan fracciones, signo y singularidad."""
    for metodo in ("laplace", "lu"):
        resultado = ControladorDeterminante.procesar_captura({"dimension": len(datos), "datos": datos, "metodo": metodo})
        assert resultado["estado"] == "EXITO"
        assert resultado["metodo"] == metodo
        assert resultado["determinante"] == esperado
        assert isinstance(resultado["determinante"], Fraction)
        assert resultado["es_singular"] is (esperado == 0)
        assert resultado["traza"][0]["matriz"].datos == Matriz(len(datos), len(datos), datos).datos
        assert resultado["traza"][-1]["detalle_latex"]


def test_igualdad_exhaustiva_orden_dos():
    """Compara ambos motores para todas las matrices 2x2 con valores -1, 0 y 1."""
    for valores in product((-1, 0, 1), repeat=4):
        matriz = Matriz(2, 2, [list(valores[:2]), list(valores[2:])])
        assert ResolutorDeterminante.resolver_laplace(matriz)["determinante"] == ResolutorDeterminante.resolver_lu(matriz)["determinante"]


def test_fila_con_ceros_preserva_indices_signos_y_acumulado():
    """La segunda fila se expande sin confundir indices originales con los del menor."""
    matriz = Matriz(3, 3, [[1, 2, 3], [0, 0, 4], [5, 6, 7]])
    resultado = ResolutorDeterminante.resolver_laplace(matriz)
    assert resultado["fila_elegida"] == 2
    assert "2 ceros" in resultado["traza"][0]["explicacion"]
    menores = [paso["menor"] for paso in resultado["traza"] if paso["tipo"] == "menor"]
    assert [menor["signo"] for menor in menores] == [-1, 1, -1]
    ultimo = menores[-1]
    assert ultimo["matriz_menor"].datos == [[1, 2], [5, 6]]
    assert ultimo["filas_originales"] == [1, 3]
    assert ultimo["columnas_originales"] == [1, 2]
    assert ultimo["valor_menor"] == -4
    assert ultimo["cofactor"] == 4
    assert ultimo["termino"] == ultimo["acumulado"] == 16
    assert [menor["acumulado"] for menor in menores] == [0, 0, 16]
    assert resultado["traza"][-2]["elemento_actual"] == (2, 3)


def test_eliminacion_preserva_estados_y_producto_con_signo():
    """El pivoteo parcial produce intercambio, pivote, operacion y cierre sin mutar A."""
    matriz = Matriz(2, 2, [[1, 2], [3, 4]])
    resultado = ResolutorDeterminante.resolver_lu(matriz)
    traza = resultado["traza"]
    assert [paso["tipo"] for paso in traza] == ["inicial", "intercambio", "pivote", "eliminacion", "pivote", "final"]
    assert traza[1]["matriz"].datos == [[3, 4], [1, 2]]
    assert traza[2]["operacion"]["valor"] == 3
    assert traza[3]["operacion"]["factor"] == Fraction(1, 3)
    assert traza[3]["matriz"].datos == [[3, 4], [0, Fraction(2, 3)]]
    assert traza[-1]["intercambios"] == 1
    assert traza[-1]["diagonal"] == [3, Fraction(2, 3)]
    assert "(-1)^s" in traza[-1]["detalle_latex"]
    assert "factorizacion LU completa" in traza[0]["explicacion"]
    assert matriz.datos == traza[0]["matriz"].datos == [[1, 2], [3, 4]]
    assert len({id(paso["matriz"]) for paso in traza}) == len(traza)


def test_limites_y_metodo_desconocido_no_cambian_la_eleccion():
    """Un rechazo de cofactores o un metodo desconocido vuelve como error explicito."""
    datos = [[int(fila == columna) for columna in range(9)] for fila in range(9)]
    for metodo in ("laplace", "desconocido"):
        resultado = ControladorDeterminante.procesar_captura({"dimension": 9, "datos": datos, "metodo": metodo})
        assert resultado["estado"] == "ERROR"
        assert "metodo" not in resultado
        assert resultado["mensaje"]


def test_presupuesto_compartido_incluye_los_menores_de_coeficiente_cero(monkeypatch):
    """El presupuesto cuenta todos los menores mostrados y aborta sin calcular otro metodo."""
    monkeypatch.setattr(cofactores, "MAXIMO_NODOS_COFACTORES", 1)
    resultado = ControladorDeterminante.procesar_captura({"dimension": 2, "datos": [[1, 0], [0, 1]], "metodo": "laplace"})
    assert resultado["estado"] == "ERROR"
    assert "presupuesto" in resultado["mensaje"]
    assert "determinante" not in resultado


def test_orden_maximo_admite_dispersion_y_rechaza_coste_denso():
    """El limite real permite identidad 8x8 y rechaza una expansion densa costosa."""
    identidad = [[int(fila == columna) for columna in range(8)] for fila in range(8)]
    resultado = ControladorDeterminante.procesar_captura({"dimension": 8, "datos": identidad, "metodo": "laplace"})
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == 1
    assert resultado["nodos"] <= cofactores.MAXIMO_NODOS_COFACTORES
    densa = [[1 for columna in range(8)] for fila in range(8)]
    rechazo = ControladorDeterminante.procesar_captura({"dimension": 8, "datos": densa, "metodo": "laplace"})
    assert rechazo["estado"] == "ERROR"
    assert "presupuesto" in rechazo["mensaje"]


def test_recomendar_no_calcula_ni_modifica_eleccion(monkeypatch):
    """Pedir recomendacion valida datos sin entrar en ninguno de los resolutores."""
    def fallar(*argumentos):
        """Detecta el calculo indebido durante una recomendacion."""
        raise AssertionError("No debe calcularse el determinante")
    monkeypatch.setattr(ResolutorDeterminante, "resolver_laplace", fallar)
    monkeypatch.setattr(ResolutorDeterminante, "resolver_lu", fallar)
    captura = {"dimension": 2, "datos": [[1, 2], [3, 4]], "metodo": "lu"}
    recomendacion = ControladorDeterminante.recomendar_captura(captura)
    assert recomendacion["metodo_recomendado"] == "laplace"
    assert captura["metodo"] == "lu"
    assert "10000" in recomendacion["limites_cofactores"]
