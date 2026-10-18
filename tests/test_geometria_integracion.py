"""Pruebas de integración de geometría, vectores, inversas y navegación."""
from tests.comun_entradas import copiar_entrada_prueba
import json
import pytest
from tests.comun import limpiar_almacen_transferencia

from src.frontend.componentes import transferencia
from src.frontend.controladores.geometria.controlador_geometria import (
    ControladorGeometria,
)
from src.frontend.controladores.operaciones_inversas.controlador_operaciones_inversas import (
    ControladorOperacionesInversas,
)
from src.frontend.controladores.operaciones_vectores.controlador_operaciones_vectores import (
    ControladorOperacionesVectores,
)
from src.frontend.navegacion import RedireccionHeredada, ubicacion_redireccion


def test_procesar_rectas_planos_fracciones_exactas():
    """Verifica procesar rectas planos fracciones exactas."""
    carga = json.dumps({
        "matriz_a": [["1001/1000", "1"], ["0", "1"]],
        "vector_b": ["1001/1000", "2"],
    })
    res = ControladorGeometria.procesar_rectas_planos(carga)
    assert res["estado"] == "EXITO"
    eq0 = res["ecuaciones"][0]
    assert eq0["coeficientes_exactos"][0] == "1001/1000"
    assert eq0["objetivo_exacto"] == "1001/1000"


def test_segmento_soluciones_infinitas_dos_dimensiones():
    """Verifica segmento soluciones infinitas dos dimensiones."""
    carga = json.dumps({
        "matriz_a": [["1", "1"], ["2", "2"]],
        "vector_b": ["2", "4"],
    })
    res = ControladorGeometria.procesar_rectas_planos(carga)
    assert res["estado"] == "EXITO"
    conjunto_solucion = res["conjunto_solucion"]
    assert conjunto_solucion is not None
    assert conjunto_solucion["tipo"] == "RECTA"
    assert conjunto_solucion["dimension"] == 1

    seg = conjunto_solucion["segmento"]
    assert seg is not None and len(seg) == 2
    h = res["rango"][1]

    for pt in seg:
        x, y = pt[0], pt[1]
        assert -h <= x <= h
        assert -h <= y <= h
        assert abs(x + y - 2.0) < 1e-9


def test_procesar_vectores_cuadro_predeterminado():
    """Verifica procesar vectores cuadro predeterminado."""
    carga = json.dumps(copiar_entrada_prueba('vectores_plano'))
    res = ControladorGeometria.procesar_vectores(carga)
    assert res["estado"] == "EXITO"
    cuadro_predeterminado = res["cuadro_predeterminado"]
    assert res["cuadros"][cuadro_predeterminado]["escalar_exacto"] == "1"


def test_almacen_traspaso_eviccion_y_limite_caracteres(monkeypatch):
    """Verifica almacen traspaso eviccion y limite caracteres."""
    limpiar_almacen_transferencia()

    contador = 1000.0

    def hora_simulada():
        """Procesa hora simulada con los datos recibidos."""
        nonlocal contador
        contador += 1.0
        return contador

    monkeypatch.setattr(transferencia, "_ahora", hora_simulada)

    tokens = []
    for _ in range(65):
        t = transferencia.guardar_matriz("test", [["1"]])
        tokens.append(t)

    assert len(transferencia._ALMACEN) <= 64
    res0 = transferencia.consumir_matriz(tokens[0], dimension_maxima=5)
    assert res0.estado == "ausente"

    celda_larga = "1" * 65
    t_mat = transferencia.guardar_matriz("test", [[celda_larga]])
    assert transferencia.consumir_matriz(t_mat, dimension_maxima=5).estado == "invalida"

    t_sys = transferencia.guardar_sistema("test", [[celda_larga]], ["1"])
    assert transferencia.consumir_sistema(t_sys, maximo_ecuaciones=5, dimensiones_permitidas={1, 2, 3}).estado == "invalida"

    t_vec = transferencia.guardar_vectores("test", "vectores", [[celda_larga, "1"]])
    assert transferencia.consumir_vectores(t_vec, dimensiones_permitidas={2, 3}).estado == "invalida"



def test_ubicacion_redireccion():
    """Verifica ubicacion redireccion."""
    regla = RedireccionHeredada(ruta="/old", ruta_destino="/new", consulta_fija=(("fixed_key", "val_fixed"),))
    entrante = [
        ("a", "1"),
        ("a", "2"),
        ("x", ""),
        ("fixed_key", "override_ignored"),
    ]
    loc = ubicacion_redireccion(regla, entrante)
    assert "fixed_key=val_fixed" in loc
    assert "override_ignored" not in loc
    assert "a=1" in loc
    assert "a=2" in loc
    assert "x=" in loc


def test_geometria_fuera_de_rango_y_segmento_invisible():
    """Verifica geometria fuera de rango y segmento invisible."""
    p1 = json.dumps({"matriz_a": [["1", "0"], ["0", "1"]], "vector_b": ["10000000000", "1"]})
    respuesta_primera = ControladorGeometria.procesar_rectas_planos(p1)
    assert respuesta_primera["fuera_de_rango"] is True

    p2 = json.dumps({"matriz_a": [["1", "1"], ["2", "2"]], "vector_b": ["10000000000", "20000000000"]})
    respuesta_segunda = ControladorGeometria.procesar_rectas_planos(p2)
    assert respuesta_segunda["conjunto_solucion"]["segmento_visible"] is False


def test_combinacion_lineal_vectores_metadatos_pasos():
    """Verifica combinacion lineal vectores metadatos pasos."""
    carga = json.dumps(copiar_entrada_prueba('combinacion_plano'))
    res_json = ControladorOperacionesVectores.procesar_combinacion_lineal(carga)
    res = json.loads(res_json)
    meta = res["metadatos_pasos"]
    pasos_gauss = res["pasos_gauss"]

    assert len(meta) == len(pasos_gauss)
    for i, m in enumerate(meta):
        assert m["indice"] == i + 1

    for s in res.get("pasos_planteamiento", []):
        assert "matriz" not in s
    for s in res.get("pasos_gauss", []):
        assert "matriz" not in s
    for s in res.get("pasos", []):
        assert "matriz" not in s


def test_inversa_construir_foco_doce_por_doce():
    """Verifica inversa construir foco doce por doce."""
    n = 12
    datos = [["2" if i == j else ("1" if i < j else "0") for j in range(n)] for i in range(n)]
    carga = json.dumps({"dimension": n, "datos": datos})
    res = ControladorOperacionesInversas.procesar_inversa(carga)
    assert res["estado"] == "EXITO"

    indices_elim = [i for i, s in enumerate(res["pasos"]) if s["tipo"] == "eliminacion"]
    assert len(indices_elim) > 0
    indice = indices_elim[0]

    foco = ControladorOperacionesInversas.construir_foco_paso(res["pasos"], indice)
    assert len(foco["filas_antes"]) > 0
    assert len(foco["filas_despues"]) > 0
    assert foco["columnas"] is not None
