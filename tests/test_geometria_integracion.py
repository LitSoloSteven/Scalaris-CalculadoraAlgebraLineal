"""Pruebas de integración de geometría, vectores, inversas y navegación."""
import json
import pytest
from tests.comun import limpiar_almacen_handoff

from src.frontend.componentes import handoff
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)
from src.frontend.controladores.operaciones_inversas.controlador_operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.controladores.operaciones_vectores.controlador_operaciones_vectores import (
    ControladorOperacionesVectores,
)
from src.frontend.navigation import LegacyRedirect, redirect_location


def test_procesar_rectas_planos_fracciones_exactas():
    payload = json.dumps({
        "matrix_A": [["1001/1000", "1"], ["0", "1"]],
        "vector_b": ["1001/1000", "2"],
    })
    res = ControladorGeometria.procesar_rectas_planos(payload)
    assert res["status"] == "OK"
    eq0 = res["equations"][0]
    assert eq0["coeffs_exact"][0] == "1001/1000"
    assert eq0["b_exact"] == "1001/1000"


def test_segmento_soluciones_infinitas_dos_dimensiones():
    payload = json.dumps({
        "matrix_A": [["1", "1"], ["2", "2"]],
        "vector_b": ["2", "4"],
    })
    res = ControladorGeometria.procesar_rectas_planos(payload)
    assert res["status"] == "OK"
    sol_set = res["set"]
    assert sol_set is not None
    assert sol_set["kind"] == "LINE"
    assert sol_set["dimension"] == 1

    seg = sol_set["segment"]
    assert seg is not None and len(seg) == 2
    h = res["range"][1]

    for pt in seg:
        x, y = pt[0], pt[1]
        assert -h <= x <= h
        assert -h <= y <= h
        assert abs(x + y - 2.0) < 1e-9


def test_procesar_vectores_cuadro_predeterminado():
    payload = json.dumps({
        "vectors": [
            {"data": ["1", "2"], "orientation": "column"},
            {"data": ["3", "4"], "orientation": "column"},
        ],
    })
    res = ControladorGeometria.procesar_vectores(payload)
    assert res["status"] == "OK"
    df = res["default_frame"]
    assert res["frames"][df]["k_exact"] == "1"


def test_almacen_traspaso_eviccion_y_limite_caracteres(monkeypatch):
    limpiar_almacen_handoff()

    contador = 1000.0

    def hora_simulada():
        nonlocal contador
        contador += 1.0
        return contador

    monkeypatch.setattr(handoff, "_ahora", hora_simulada)

    tokens = []
    for _ in range(65):
        t = handoff.guardar_matriz("test", [["1"]])
        tokens.append(t)

    assert len(handoff._ALMACEN) <= 64
    res0 = handoff.consumir_matriz(tokens[0], max_n=5)
    assert res0.status == "missing"

    celda_larga = "1" * 65
    t_mat = handoff.guardar_matriz("test", [[celda_larga]])
    assert handoff.consumir_matriz(t_mat, max_n=5).status == "invalid"

    t_sys = handoff.guardar_sistema("test", [[celda_larga]], ["1"])
    assert handoff.consumir_sistema(t_sys, max_m=5, allowed_n={1, 2, 3}).status == "invalid"

    t_vec = handoff.guardar_vectores("test", "vectores", [[celda_larga, "1"]])
    assert handoff.consumir_vectores(t_vec, allowed_n={2, 3}).status == "invalid"



def test_ubicacion_redireccion():
    regla = LegacyRedirect(path="/old", target_route="/new", fixed_query=(("fixed_key", "val_fixed"),))
    entrante = [
        ("a", "1"),
        ("a", "2"),
        ("x", ""),
        ("fixed_key", "override_ignored"),
    ]
    loc = redirect_location(regla, entrante)
    assert "fixed_key=val_fixed" in loc
    assert "override_ignored" not in loc
    assert "a=1" in loc
    assert "a=2" in loc
    assert "x=" in loc


def test_geometria_fuera_de_rango_y_segmento_invisible():
    p1 = json.dumps({"matrix_A": [["1", "0"], ["0", "1"]], "vector_b": ["10000000000", "1"]})
    r1 = ControladorGeometria.procesar_rectas_planos(p1)
    assert r1["out_of_range"] is True

    p2 = json.dumps({"matrix_A": [["1", "1"], ["2", "2"]], "vector_b": ["10000000000", "20000000000"]})
    r2 = ControladorGeometria.procesar_rectas_planos(p2)
    assert r2["set"]["segment_visible"] is False


def test_combinacion_lineal_vectores_metadatos_pasos():
    payload = json.dumps({
        "b": {"data": ["5", "6"], "orientation": "column"},
        "vectors": [
            {"data": ["1", "0"], "orientation": "column"},
            {"data": ["0", "1"], "orientation": "column"},
        ],
    })
    res_json = ControladorOperacionesVectores.procesar_combinacion_lineal(payload)
    res = json.loads(res_json)
    meta = res["steps_meta"]
    gauss_steps = res["gauss_steps"]

    assert len(meta) == len(gauss_steps)
    for i, m in enumerate(meta):
        assert m["index"] == i + 1

    for s in res.get("setup_steps", []):
        assert "matrix" not in s
    for s in res.get("gauss_steps", []):
        assert "matrix" not in s
    for s in res.get("steps", []):
        assert "matrix" not in s


def test_inversa_construir_foco_doce_por_doce():
    n = 12
    datos = [["2" if i == j else ("1" if i < j else "0") for j in range(n)] for i in range(n)]
    payload = json.dumps({"n": n, "data": datos})
    res = ControladorOperacionesInversas.procesar_inversa(payload)
    assert res["status"] == "SUCCESS"

    indices_elim = [i for i, s in enumerate(res["steps"]) if s["kind"] == "eliminacion"]
    assert len(indices_elim) > 0
    idx = indices_elim[0]

    foco = ControladorOperacionesInversas.construir_foco_paso(res["steps"], idx)
    assert len(foco["rows_before"]) > 0
    assert len(foco["rows_after"]) > 0
    assert foco["cols"] is not None
