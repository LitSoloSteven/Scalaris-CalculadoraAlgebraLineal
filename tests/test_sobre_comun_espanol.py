"""Contrato único del sobre y conservación de valores exactos al presentarlo."""
import json
from fractions import Fraction
from types import SimpleNamespace

import pytest
from nicegui import ui

from src.backend.modelos.matriz import Matriz
from src.backend.resolutores.trazado import TrazadorPasos
from src.frontend.componentes.reproductor_pasos.modelo import PasoReproductor
from src.frontend.controladores.utilidades import parsear_carga_json
from src.frontend.vistas.operaciones_matrices._cuerpo_reproductor_matrices import renderizar_cuerpo_matrices
from tests.comun_caracterizacion_backend import ejecutar_caso
from tests.test_caracterizacion_backend import CASOS

CLAVES_RETIRADAS = {
    "status", "message", "steps", "description", "matrix", "detail_latex", "explanation",
    "kind", "index", "op", "detail", "rows_before", "rows_after", "cols", "pivot",
    "rows_changed", "swap_rows", "groups", "stats", "title", "summary", "step_indices",
    "group_index",
}
ESTADOS_RETIRADOS = {"SUCCESS", "OK", "UNIQUE", "INFINITE", "UNIQUE_SOLUTION",
                     "INFINITE_SOLUTIONS", "NO_SOLUTION"}


def _comprobar_sobre(valor):
    if isinstance(valor, dict):
        assert CLAVES_RETIRADAS.isdisjoint(valor)
        if "estado" in valor:
            assert valor["estado"] not in ESTADOS_RETIRADOS
        for contenido in valor.values():
            _comprobar_sobre(contenido)
    elif isinstance(valor, list):
        for contenido in valor:
            _comprobar_sobre(contenido)


@pytest.mark.parametrize("caso", CASOS, ids=lambda caso: caso["nombre"])
def test_resolutores_publican_solo_el_sobre_espanol(caso):
    """Las doce familias emiten el sobre canónico incluso en entradas desfavorables."""
    _comprobar_sobre(ejecutar_caso(caso))


@pytest.mark.parametrize("carga", ["{", "[]", "null"])
def test_error_parseo_solo_publica_estado_y_mensaje(carga):
    """Los errores JSON tienen un único estado y mensaje sin campos heredados."""
    datos, error = parsear_carga_json(carga)
    assert datos is None
    sobre = json.loads(error)
    assert set(sobre) == {"estado", "mensaje"}
    assert sobre["estado"] == "ERROR"
    assert sobre["mensaje"]


def test_trazador_conserva_fraccion_y_copia_defensiva():
    """El paso captura la matriz exacta antes de que el productor vuelva a editarla."""
    valor = Fraction(123456789012345678901, 987654321098765432109)
    matriz = Matriz(1, 1, [[valor]])
    trazador = TrazadorPasos()
    trazador._registrar_paso("Texto literal", matriz, r"\frac{1}{2}")
    matriz.establecer(0, 0, 9)
    paso = trazador.pasos[0]
    assert set(paso) == {"descripcion", "matriz", "detalle_latex"}
    assert paso["matriz"].obtener(0, 0) == valor
    assert paso["descripcion"] == "Texto literal"
    assert paso["detalle_latex"] == r"\frac{1}{2}"


def test_cuerpo_matrices_conserva_indice_y_carga_detalle_una_vez(monkeypatch):
    """La ausencia de operación usa el índice del objeto y el detalle no se duplica."""
    modulo = "src.frontend.vistas.operaciones_matrices._cuerpo_reproductor_matrices"
    expresiones = []
    monkeypatch.setattr(modulo + ".renderizar_latex", expresiones.append)
    contenedor = ui.column()
    try:
        paso = PasoReproductor(2, "operacion", "", cuerpo={
            "pasos_celda_a_celda": [{"detalle_latex": "1+2=3"}, {"detalle_latex": ""}],
        })
        renderizar_cuerpo_matrices(paso, contenedor)
        expansion = next(elemento for elemento in contenedor.descendants()
                         if isinstance(elemento, ui.expansion))
        manejador = expansion._change_handlers[0]
        manejador(SimpleNamespace(value=False))
        manejador(SimpleNamespace(value=True))
        manejador(SimpleNamespace(value=True))
        assert expresiones == [r"\text{Paso 3}", "1+2=3"]
    finally:
        contenedor.delete()
