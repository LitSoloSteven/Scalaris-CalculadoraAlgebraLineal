"""Pruebas unitarias para el controlador de operaciones de inversión matricial."""
import json
from src.frontend.controladores.operaciones_inversas import (
    ControladorOperacionesInversas,
)


def test_controlador_inversa_dos_por_dos_exitoso():
    """Valida el cálculo de inversa 2x2, determinante y generación de pasos."""
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["3", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert res["status"] == "SUCCESS"
    assert res["determinant_str"] == "-2"
    assert res["matrix_a"] is not None
    assert res["matrix_a_latex"] is not None
    assert res["inverse"] is not None
    assert res["inverse_latex"] is not None
    assert len(res["verifications"]) == 3
    assert all(v["coincide"] is True for v in res["verifications"])

    steps = res["steps"]
    groups = res["groups"]
    stats = res["stats"]

    assert len(steps) > 0
    kinds = {s["kind"] for s in steps}
    assert "inicial" in kinds
    assert "pivote" in kinds
    assert "eliminacion" in kinds
    assert "normalizacion" in kinds
    assert "otro" not in kinds

    for s in steps:
        g_idx = s["group_index"]
        assert 0 <= g_idx < len(groups)
        assert s["index"] in groups[g_idx]["step_indices"]

    assert stats["total"] == len(steps)
    assert stats["pivotes"] > 0
    assert stats["eliminaciones"] > 0
    assert stats["normalizaciones"] > 0


def test_controlador_inversa_celda_invalida_reporta_coordenadas():
    """Verifica que se identifique con precisión la coordenada de celda inválida."""
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["abc", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert res["status"] == "ERROR"
    assert res["error_cell"] == [1, 0]
    assert "Error en A[2,1]" in res["message"]


def test_controlador_inversa_limite_dimension():
    """Rechaza dimensiones que exceden el tamaño máximo permitido."""
    payload_n51 = json.dumps({
        "n": 51,
        "data": [["0"] * 51] * 51,
    })
    res_n51 = ControladorOperacionesInversas.procesar_inversa(payload_n51)
    assert res_n51["status"] == "ERROR"
    assert "entre 1 y 50" in res_n51["message"]


def test_controlador_inversa_json_malformado():
    """Rechaza strings que no cumplen formato JSON o no son diccionarios."""
    res_malformed = ControladorOperacionesInversas.procesar_inversa("not json")
    assert res_malformed["status"] == "ERROR"

    res_not_dict = ControladorOperacionesInversas.procesar_inversa("[1, 2, 3]")
    assert res_not_dict["status"] == "ERROR"


def test_controlador_inversa_matriz_singular():
    """Identifica matrices cuadradas con determinante cero como singulares."""
    payload = json.dumps({
        "n": 2,
        "data": [["1", "2"], ["2", "4"]],
    })
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert res["status"] == "SINGULAR"
    assert res["determinant"] == 0
    assert res["inverse"] is None
