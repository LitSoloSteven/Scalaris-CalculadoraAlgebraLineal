"""Auditoria explicita de los archivos nuevos del motor de regla falsa."""
import ast
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RAICES = RAIZ / "src" / "backend" / "resolutores" / "raices"
TESTS = RAIZ / "tests"


def _archivos_produccion():
    return sorted(RAICES.glob("*regla_falsa*.py"))


def _archivos_test():
    return sorted(TESTS.glob("test_regla_falsa_*.py"))


@pytest.mark.parametrize("ruta", _archivos_produccion(), ids=lambda r: r.name)
def test_archivo_produccion_por_debajo_de_300_lineas(ruta):
    """Cada archivo nuevo del motor respeta el máximo de 300 líneas."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert len(lineas) <= 300, f"{ruta.name} tiene {len(lineas)} líneas"


@pytest.mark.parametrize("ruta", _archivos_test(), ids=lambda r: r.name)
def test_archivo_test_por_debajo_de_300_lineas(ruta):
    """Cada archivo de pruebas nuevo respeta el máximo de 300 líneas."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    assert len(lineas) <= 300, f"{ruta.name} tiene {len(lineas)} líneas"


@pytest.mark.parametrize("ruta", _archivos_produccion(), ids=lambda r: r.name)
def test_funciones_respetan_40_lineas_y_5_parametros(ruta):
    """Ninguna función del motor supera 40 líneas ni 5 parámetros."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            longitud = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
            assert longitud <= 40, f"{ruta.name}::{nodo.name} tiene {longitud} líneas"
            n_parametros = (
                len(nodo.args.posonlyargs)
                + len(nodo.args.args)
                + len(nodo.args.kwonlyargs)
            )
            assert n_parametros <= 5, f"{ruta.name}::{nodo.name} tiene {n_parametros} parámetros"


@pytest.mark.parametrize("ruta", _archivos_produccion(), ids=lambda r: r.name)
def test_clases_respetan_200_lineas(ruta):
    """Ninguna clase del motor supera 200 líneas."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ClassDef):
            longitud = (nodo.end_lineno or nodo.lineno) - nodo.lineno + 1
            assert longitud <= 200, f"{ruta.name}::{nodo.name} tiene {longitud} líneas"



def _nombres_importados(arbol: ast.AST) -> list[str]:
    """Recoge los módulos importados para que el test no anide dos bucles."""
    nombres: list[str] = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            nombres.append(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            nombres.extend(alias.name for alias in nodo.names)
    return nombres


@pytest.mark.parametrize("ruta", _archivos_produccion(), ids=lambda r: r.name)
def test_motor_no_importa_capas_prohibidas(ruta):
    """Los archivos de raíces no importan frontend, IA, NiceGUI ni Plotly."""
    prohibidas = ("src.frontend", "src.ai", "nicegui", "plotly")
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    for nombre in _nombres_importados(arbol):
        assert not any(nombre.startswith(p) for p in prohibidas), f"{ruta.name} importa {nombre}"