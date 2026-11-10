"""Auditoría del código extraído sin alterar los manifiestos existentes."""
import ast

import pytest

from tests.comun import RAIZ
from tests import test_cumplimiento_reglas as reglas

_COMPARTIDOS = (
    "componentes/candidatos_raices.py", "componentes/captura_exploracion_raices.py",
    "componentes/exploracion_raices.py", "controladores/coordinacion_trabajos_raices.py",
    "controladores/exploracion_raices.py", "controladores/formato_numerico_raices.py",
    "controladores/rango_exploracion_raices.py",
)
_FACHADAS = (
    "controladores/biseccion/exploracion.py", "controladores/biseccion/presentacion.py",
    "controladores/biseccion/presentacion_diagnostico.py", "controladores/biseccion/vista_previa.py",
    "vistas/biseccion/candidatos.py", "vistas/biseccion/exploracion.py", "vistas/biseccion/rango_grafica.py",
)


@pytest.mark.parametrize("comprobar", [
    reglas.test_limites_tamanio_y_complejidad, reglas.test_docstrings_publicos,
    reglas.test_identificadores_idioma_y_ascii, reglas.test_comentarios_y_textos_limpios,
    reglas.test_reglas_python_frontend,
])
def test_archivos_compartidos_y_fachadas_cumplen_reglas(monkeypatch, comprobar):
    """Aplica la auditoría existente a todos los archivos de producción afectados."""
    rutas = tuple(RAIZ / "src/frontend" / ruta for ruta in _COMPARTIDOS + _FACHADAS)
    monkeypatch.setattr(reglas, "RUTAS_AUDITADAS", rutas)
    comprobar()


@pytest.mark.parametrize("ruta", _COMPARTIDOS)
def test_modulos_neutrales_no_importan_vistas_ni_biseccion(ruta):
    """La reutilización no depende del consumidor concreto ni de su algoritmo."""
    arbol = ast.parse((RAIZ / "src/frontend" / ruta).read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulo = nodo.module or ""
            assert ".vistas." not in modulo and ".biseccion." not in modulo
            assert not nodo.level
