"""Limites de dimension, presupuesto y entradas no exactas de la adjunta."""
from fractions import Fraction

import pytest

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.determinante import cofactores
from src.backend.resolutores.operaciones_matrices.determinante.cofactores import (
    ExpansionCofactores,
)
from src.backend.resolutores.operaciones_matrices.inversa.inversa import ResolutorInversa
from src.backend.resolutores.operaciones_matrices.inversa.inversa_adjunta import (
    calcular_inversa_adjunta,
)


def test_expansion_conserva_calcular_y_suma_el_presupuesto():
    """La API aditiva conserva las claves historicas y acumula nodos por instancia."""
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expansor = ExpansionCofactores()
    assert expansor.calcular_valor(matriz) == Fraction(0)
    nodos_previos = expansor.nodos
    historico = expansor.calcular(matriz)
    assert set(historico) == {"fila", "menores", "determinante", "nodos"}
    assert historico["determinante"] == Fraction(0)
    assert expansor.nodos > nodos_previos


def test_presupuesto_compartido_entre_llamadas_del_mismo_expansor(monkeypatch):
    """La segunda llamada agota el contador iniciado por la primera."""
    monkeypatch.setattr(cofactores, "MAXIMO_NODOS_COFACTORES", 5)
    matriz = Matriz(3, 3, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    expansor = ExpansionCofactores()
    expansor.calcular_valor(matriz)
    with pytest.raises(cofactores.ErrorPresupuestoCofactores) as captura:
        expansor.calcular_valor(matriz)
    assert captura.value.nodos > captura.value.limite == 5


def test_identidad_ocho_por_ocho_dentro_del_presupuesto():
    """El limite real permite una matriz dispersa de orden 8."""
    datos = [[int(fila == columna) for columna in range(8)] for fila in range(8)]
    resultado = calcular_inversa_adjunta(Matriz(8, 8, datos))
    assert resultado["estado"] == "EXITO"
    assert resultado["determinante"] == Fraction(1)
    assert resultado["inversa"].datos == datos
    assert resultado["nodos_cofactores"] <= resultado["limite_nodos"]


def test_matriz_densa_ocho_por_ocho_agota_el_presupuesto_real():
    """El presupuesto configurado se comparte entre todos los menores."""
    datos = [[1 for _ in range(8)] for _ in range(8)]
    resultado = calcular_inversa_adjunta(Matriz(8, 8, datos))
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "PRESUPUESTO_COFACTORES_EXCEDIDO"
    assert resultado["nodos_cofactores"] > resultado["limite_nodos"]
    assert resultado["menores"] is None
    assert resultado["inversa"] is None


def test_presupuesto_inyectado_informa_consumo_y_limite(monkeypatch):
    """Un presupuesto pequeno y determinista informa el intento excedido."""
    monkeypatch.setattr(cofactores, "MAXIMO_NODOS_COFACTORES", 3)
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[1, 2], [3, 4]]))
    assert resultado["codigo"] == "PRESUPUESTO_COFACTORES_EXCEDIDO"
    assert resultado["limite_nodos"] == 3
    assert resultado["nodos_cofactores"] == 4


def test_orden_nueve_se_rechaza_sin_calcular_menores():
    """El metodo por adjunta no reduce el limite de la inversion heredada."""
    datos = [[int(fila == columna) for columna in range(9)] for fila in range(9)]
    resultado = calcular_inversa_adjunta(Matriz(9, 9, datos))
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "DIMENSION_ADJUNTA_EXCEDIDA"
    assert resultado["menores"] is None
    assert resultado["adjunta"] is None


def test_entrada_que_no_es_matriz_devuelve_error_completo():
    """El motor no accede a atributos de una entrada desconocida."""
    resultado = calcular_inversa_adjunta(object())
    assert resultado["estado"] == "ERROR"
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert resultado["dimension"] == 0


def test_forma_rectangular_se_rechaza():
    """La inversa por adjunta exige una matriz cuadrada."""
    resultado = calcular_inversa_adjunta(Matriz(2, 3, [[1, 2, 3], [4, 5, 6]]))
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert "cuadrada" in resultado["mensaje"]


@pytest.mark.parametrize("valor", [True, False, 1e-5])
def test_celdas_booleanas_o_flotantes_residuales_se_rechazan(valor):
    """Un booleano o un flotante no exacto no se interpreta como escalar."""
    resultado = calcular_inversa_adjunta(Matriz(1, 1, [[valor]]))
    assert resultado["codigo"] == "ENTRADA_INVALIDA"
    assert "fracciones exactas" in resultado["mensaje"]


def test_gauss_jordan_heredado_sigue_disponible():
    """La ruta antigua conserva su determinante e inversa sin cambios."""
    resultado = ResolutorInversa().resolver(Matriz(2, 2, [[1, 2], [3, 4]]))
    assert resultado["determinante"] == Fraction(-2)
    assert resultado["inversa"].datos == [[-2, 1], [Fraction(3, 2), Fraction(-1, 2)]]
