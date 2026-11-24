"""Traza, instantaneas y representacion del menor vacio en la adjunta."""
from fractions import Fraction

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.operaciones_matrices.inversa.inversa_adjunta import (
    calcular_inversa_adjunta,
)

CLAVES_PASO = {
    "indice", "tipo", "descripcion", "explicacion", "matriz",
    "coordenada", "valor", "detalle",
}


def test_traza_tiene_un_cofactor_por_celda_y_claves_completas():
    """La matriz 3x3 produce nueve cofactores con indices consecutivos."""
    resultado = calcular_inversa_adjunta(Matriz(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]]))
    pasos = resultado["traza"]
    assert [paso["indice"] for paso in pasos] == list(range(len(pasos)))
    assert all(set(paso) == CLAVES_PASO for paso in pasos)
    cofactores = [paso for paso in pasos if paso["tipo"] == "cofactor"]
    assert len(cofactores) == 9
    assert [paso["coordenada"] for paso in cofactores] == [
        (fila, columna) for fila in range(3) for columna in range(3)
    ]


def test_menor_elimina_fila_y_columna_y_conserva_indices_originales():
    """Cada menor coincide con la submatriz y la coordenada en base cero."""
    matriz = Matriz(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]])
    resultado = calcular_inversa_adjunta(matriz)
    detalles = {(detalle["fila"], detalle["columna"]): detalle
                for detalle in resultado["detalle_cofactores"]}
    for paso in (paso for paso in resultado["traza"] if paso["tipo"] == "cofactor"):
        detalle = detalles[paso["coordenada"]]
        assert paso["matriz"].datos == detalle["matriz_menor"].datos
        assert paso["matriz"].filas == 2
        assert detalle["filas_originales"] == tuple(
            indice for indice in range(3) if indice != detalle["fila"]
        )
    assert detalles[(0, 0)]["matriz_menor"].datos == [[1, 4], [6, 0]]


def test_signos_y_valores_de_los_cuatro_cofactores():
    """El signo alterna por coordenada y no por la posicion renumerada del menor."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[1, 2], [3, 4]]))
    pasos = [paso for paso in resultado["traza"] if paso["tipo"] == "cofactor"]
    assert [paso["coordenada"] for paso in pasos] == [(0, 0), (0, 1), (1, 0), (1, 1)]
    assert [paso["valor"] for paso in pasos] == [4, -3, -2, 1]
    assert [detalle["signo"] for detalle in resultado["detalle_cofactores"]] == [1, -1, -1, 1]


def test_menor_vacio_del_orden_uno_no_crea_matriz_cero_por_cero():
    """La traza documenta la convencion del menor vacio con matriz ausente."""
    resultado = calcular_inversa_adjunta(Matriz(1, 1, [[2]]))
    paso = next(paso for paso in resultado["traza"] if paso["tipo"] == "cofactor")
    detalle = resultado["detalle_cofactores"][0]
    assert detalle["menor_vacio"] is True
    assert detalle["valor_menor"] == Fraction(1)
    assert detalle["cofactor"] == Fraction(1)
    assert detalle["matriz_menor"] is None
    assert paso["matriz"] is None
    assert paso["coordenada"] == (0, 0)
    assert "vacio" in paso["detalle"]


def test_instantaneas_de_la_traza_no_comparten_matrices_mutables():
    """Modificar un paso no altera los detalles ni las matrices del resultado."""
    resultado = calcular_inversa_adjunta(Matriz(3, 3, [[1, 2, 3], [0, 1, 4], [5, 6, 0]]))
    paso = next(paso for paso in resultado["traza"] if paso["tipo"] == "cofactor")
    original = resultado["detalle_cofactores"][0]["matriz_menor"].datos
    paso["matriz"].establecer(0, 0, 999)
    assert resultado["detalle_cofactores"][0]["matriz_menor"].datos == original
    resultado["menores"].establecer(0, 0, 999)
    assert resultado["detalle_cofactores"][0]["valor_menor"] == Fraction(-24)


def test_expansion_elige_la_fila_con_mas_ceros():
    """La traza nombra la fila elegida y conserva la igualdad exacta."""
    resultado = calcular_inversa_adjunta(Matriz(3, 3, [[1, 2, 3], [0, 0, 4], [5, 6, 7]]))
    paso = next(paso for paso in resultado["traza"] if paso["tipo"] == "determinante")
    assert "fila 2" in paso["descripcion"]
    assert resultado["determinante"] == Fraction(16)
    assert paso["valor"] == Fraction(16)


def test_singular_completa_sin_division_y_con_conclusion():
    """La singularidad conserva cofactores, adjunta y verificacion sin inversa."""
    resultado = calcular_inversa_adjunta(Matriz(2, 2, [[1, 2], [2, 4]]))
    tipos = [paso["tipo"] for paso in resultado["traza"]]
    assert tipos.count("cofactor") == 4
    assert "division" in tipos and tipos[-1] == "conclusion"
    assert resultado["traza"][-1]["descripcion"].lower().endswith("singular")
    assert resultado["inversa"] is None


def test_error_no_presenta_resultado_parcial():
    """Un rechazo de dimension deja vacias las colecciones de procedimiento."""
    datos = [[int(fila == columna) for columna in range(9)] for fila in range(9)]
    resultado = calcular_inversa_adjunta(Matriz(9, 9, datos))
    assert resultado["traza"] == ()
    assert resultado["detalle_cofactores"] == ()
    assert resultado["comprobaciones"] == ()
    assert resultado["determinante"] is None
    assert resultado["menores"] is None
