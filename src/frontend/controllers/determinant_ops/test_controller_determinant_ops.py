"""Pruebas unitarias para el controlador de determinantes."""
from __future__ import annotations

from fractions import Fraction
import json

from src.frontend.controllers.determinant_ops import DeterminantOpsController
from src.frontend.controllers.determinant_ops._foco import foco_paso


def _ejecutar(n: int, data: list[list[str]], metodo: str) -> dict:
    """Envuelve la llamada a process_determinant con serialización JSON."""
    payload = json.dumps({"n": n, "data": data, "metodo": metodo})
    return DeterminantOpsController.process_determinant(payload)


def _verificar_invariantes_pasos(res: dict) -> None:
    """Comprueba índices consecutivos, grupos válidos y conteo total de pasos."""
    pasos = res["steps"]
    grupos = res["groups"]
    assert res["stats"]["total"] == len(pasos)
    for idx, paso in enumerate(pasos):
        assert paso["index"] == idx
        assert 0 <= paso["group_index"] < len(grupos)
    indices_en_grupos = [i for g in grupos for i in g["step_indices"]]
    assert sorted(indices_en_grupos) == list(range(len(pasos)))


def test_matriz_2x2_ambos_metodos() -> None:
    """Verifica [[1,2],[3,4]] en cofactores y LU con det = -2."""
    datos = [["1", "2"], ["3", "4"]]
    for metodo in ("cofactores", "lu"):
        res = _ejecutar(2, datos, metodo)
        assert res["status"] == "SUCCESS"
        assert res["determinante"] == Fraction(-2)
        assert res["determinante_str"] == "-2"
        assert res["es_singular"] is False
        _verificar_invariantes_pasos(res)


def test_matriz_3x3_ambos_metodos_y_verificaciones() -> None:
    """Verifica [[1,2,3],[4,5,6],[7,8,10]] con det = -3 y verificaciones exactas."""
    datos = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "10"]]
    for metodo in ("cofactores", "lu"):
        res = _ejecutar(3, datos, metodo)
        assert res["status"] == "SUCCESS"
        assert res["determinante"] == Fraction(-3)
        assert len(res["verifications"]) >= 1
        assert all(v["coincide"] is True for v in res["verifications"])
        _verificar_invariantes_pasos(res)


def test_matrices_singulares() -> None:
    """Verifica detección de singularidad en matrices 2×2 y 3×3."""
    casos = [
        (2, [["1", "2"], ["2", "4"]]),
        (3, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]),
    ]
    for n, datos in casos:
        res_cof = _ejecutar(n, datos, "cofactores")
        assert res_cof["status"] == "SINGULAR"
        assert res_cof["es_singular"] is True
        assert res_cof["determinante"] == Fraction(0)

        res_lu = _ejecutar(n, datos, "lu")
        assert res_lu["status"] == "SINGULAR"
        assert res_lu["es_singular"] is True
        assert res_lu["steps"][-1]["kind"] == "singular"
        _verificar_invariantes_pasos(res_lu)


def test_matriz_1x1_ambos_metodos() -> None:
    """Verifica caso base 1×1 con un único paso final."""
    for metodo in ("cofactores", "lu"):
        res = _ejecutar(1, [["5"]], metodo)
        assert res["status"] == "SUCCESS"
        assert res["determinante"] == Fraction(5)
        assert len(res["steps"]) == 1
        assert res["steps"][0]["kind"] == "final"
        _verificar_invariantes_pasos(res)


def test_intercambio_filas_lu() -> None:
    """Verifica registro de intercambio de filas en [[0,1],[1,0]] con LU."""
    res = _ejecutar(2, [["0", "1"], ["1", "0"]], "lu")
    assert res["status"] == "SUCCESS"
    assert res["determinante"] == Fraction(-1)
    assert res["stats"]["intercambios"] == 1
    assert any(p["kind"] == "intercambio" for p in res["steps"])
    _verificar_invariantes_pasos(res)


def test_cofactores_con_coeficiente_cero() -> None:
    """Verifica conteo de términos nulos en la primera fila para cofactores."""
    res = _ejecutar(2, [["0", "1"], ["2", "3"]], "cofactores")
    assert res["status"] == "SUCCESS"
    assert res["determinante"] == Fraction(-2)
    assert res["stats"]["terminos_cero"] == 1
    _verificar_invariantes_pasos(res)


def test_fracciones_denominador_grande() -> None:
    """Verifica preservación exacta de denominadores de 4 dígitos."""
    datos = [["1/1001", "0"], ["0", "1000/7"]]
    for metodo in ("cofactores", "lu"):
        res = _ejecutar(2, datos, metodo)
        assert res["status"] == "SUCCESS"
        assert res["determinante"] == Fraction(1000, 7007)
        assert res["determinante_str"] == "1000/7007"


def test_errores_validacion_y_limites() -> None:
    """Verifica celdas inválidas, notación científica, límites de n y JSON inválido."""
    res_abc = _ejecutar(2, [["1", "2"], ["abc", "4"]], "cofactores")
    assert res_abc["status"] == "ERROR"
    assert res_abc["error_cell"] == [1, 0]

    res_sci = _ejecutar(2, [["1e5", "2"], ["3", "4"]], "lu")
    assert res_sci["status"] == "ERROR"
    assert res_sci["error_cell"] == [0, 0]

    m9 = [["1" if i == j else "0" for j in range(9)] for i in range(9)]
    assert _ejecutar(9, m9, "cofactores")["status"] == "ERROR"

    m51 = [["1" if i == j else "0" for j in range(51)] for i in range(51)]
    assert _ejecutar(51, m51, "lu")["status"] == "ERROR"

    assert _ejecutar(2, [["1", "0"], ["0", "1"]], "invalido")["status"] == "ERROR"
    assert DeterminantOpsController.process_determinant("{mal")["status"] == "ERROR"
    assert DeterminantOpsController.process_determinant("[1, 2]")["status"] == "ERROR"


def test_recomendacion_por_dimension() -> None:
    """Verifica que recomendar sugiere cofactores para n=3 y lu para n=7."""
    rec_3 = DeterminantOpsController.recomendar(3)
    rec_7 = DeterminantOpsController.recomendar(7)
    assert rec_3["recommended"] == "cofactores"
    assert rec_7["recommended"] == "lu"


def test_foco_paso_seguro_y_recorte_columnas() -> None:
    """Verifica que foco_paso no lanza con índices fuera de rango y recorta a n columnas."""
    res = _ejecutar(3, [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "10"]], "lu")
    vacio = foco_paso(res["steps"], 999, 3, "lu")
    assert vacio["rows_before"] == {}

    for idx in range(len(res["steps"])):
        foco = DeterminantOpsController.build_focus_for_step(res, idx)
        for fila in foco["rows_before"].values():
            assert len(fila) <= 3
        for fila in foco["rows_after"].values():
            assert len(fila) <= 3


def test_identidad_20x20_lu() -> None:
    """Verifica matriz identidad 20×20 mediante LU con det = 1."""
    identidad = [["1" if i == j else "0" for j in range(20)] for i in range(20)]
    res = _ejecutar(20, identidad, "lu")
    assert res["status"] == "SUCCESS"
    assert res["determinante"] == Fraction(1)
    assert res["determinante_str"] == "1"